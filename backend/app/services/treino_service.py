"""Trilha de treino do aluno: exercício sob medida para o erro que ele repete.

O painel de erros recorrentes já dizia ao aluno **o que** ele repete. Esta é a
resposta para **o que fazer com isso**. A trilha olha as categorias que ele mais
erra, gera exercício para a primeira delas e libera treino ilimitado ali.

Três decisões de produto moram aqui:

- **Nunca vale nota**, então não passa por fila de revisão do professor. Preserva
  o treino às duas da manhã, que é quando o aluno de CS1 estuda. O preço é que o
  aluno pode reportar exercício ruim, e reportado sai da trilha.
- **Tentativas ilimitadas**, sem janela e sem teto, porque é treino.
- **Teto de custo na geração**, não no treino: gerar é chamada de LLM por aluno,
  treinar no que já existe é de graça.
"""
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.engine.evaluators.code_evaluator import evaluate_code
from app.llm.exercise_generator import GERACOES_POR_DIA, ExercicioInvalido, gerar_exercicio
from app.models.orm import ExercicioGerado, Student, Submission, TentativaDeTreino

CATEGORIA_CORRETA = "Correto"


class TreinoIndisponivel(RuntimeError):
    """Nada a gerar agora, com o motivo em texto para o aluno ler."""


# ── o que treinar ────────────────────────────────────────────────────────────

def categorias_para_treinar(student: Student, db: Session) -> list[dict]:
    """As categorias que o aluno mais erra, da mais frequente para a menos.

    Sai das submissões reais dele, então é a mesma fonte do painel de erros
    recorrentes. Sem chamada de LLM."""
    submissoes = (
        db.query(Submission)
        .filter(Submission.student_id == student.id)
        .order_by(Submission.submitted_at, Submission.id)
        .all()
    )
    por_categoria: dict[str, list[Submission]] = defaultdict(list)
    for s in submissoes:
        if s.error_category and s.error_category != CATEGORIA_CORRETA:
            por_categoria[s.error_category].append(s)

    gerados = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.reportado.is_(False))
        .all()
    )
    por_cat_gerados: dict[str, list[ExercicioGerado]] = defaultdict(list)
    for e in gerados:
        por_cat_gerados[e.error_category].append(e)

    categorias = []
    for categoria, ocorrencias in por_categoria.items():
        exercicios = por_cat_gerados.get(categoria, [])
        categorias.append({
            "error_category": categoria,
            "ocorrencias": len(ocorrencias),
            "o_que_fazer": ocorrencias[-1].actionable_feedback or "",
            "exercicios_gerados": len(exercicios),
            "exercicios_resolvidos": sum(1 for e in exercicios if e.resolvido),
            "tem_pendente": any(not e.resolvido for e in exercicios),
        })
    categorias.sort(key=lambda c: -c["ocorrencias"])
    return categorias


def trilha(student: Student, db: Session) -> dict:
    exercicios = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.reportado.is_(False))
        .order_by(ExercicioGerado.created_at.desc())
        .all()
    )
    return {
        "categorias": categorias_para_treinar(student, db),
        "exercicios": [_exercicio_resumo(e) for e in exercicios],
        "geracoes_restantes_hoje": _restantes_hoje(student, db),
    }


# ── geração ──────────────────────────────────────────────────────────────────

def _restantes_hoje(student: Student, db: Session) -> int:
    desde = datetime.utcnow() - timedelta(days=1)
    usadas = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.created_at >= desde)
        .count()
    )
    return max(0, GERACOES_POR_DIA - usadas)


def gerar_para_categoria(student: Student, categoria: str | None, db: Session) -> dict:
    """Gera um exercício para a categoria pedida, ou para a que o aluno mais erra.

    Antes de gastar uma chamada de LLM, devolve o exercício pendente que já
    existe naquela categoria: treinar o que está aberto vale mais do que
    acumular exercício novo, e é de graça."""
    categorias = categorias_para_treinar(student, db)
    if not categorias:
        raise TreinoIndisponivel(
            "Você ainda não tem erros suficientes para a trilha. "
            "Resolva alguma questão da sua turma e volte aqui.")

    if categoria:
        alvo = next((c for c in categorias if c["error_category"] == categoria), None)
        if not alvo:
            raise TreinoIndisponivel("Você não tem erros nessa categoria.")
    else:
        alvo = next((c for c in categorias if not c["tem_pendente"]), categorias[0])

    pendente = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.error_category == alvo["error_category"],
                ExercicioGerado.resolvido.is_(False),
                ExercicioGerado.reportado.is_(False))
        .order_by(ExercicioGerado.created_at.desc())
        .first()
    )
    if pendente:
        return _exercicio_detalhe(pendente, db, reaproveitado=True)

    if _restantes_hoje(student, db) <= 0:
        raise TreinoIndisponivel(
            f"Você já gerou {GERACOES_POR_DIA} exercícios nas últimas 24 horas. "
            "Treinar nos que já estão aqui continua liberado.")

    ja_vistos = [
        e.enunciado for e in db.query(ExercicioGerado).filter(
            ExercicioGerado.student_id == student.id,
            ExercicioGerado.error_category == alvo["error_category"]).all()
    ]
    try:
        dados = gerar_exercicio(alvo["error_category"], alvo["o_que_fazer"], ja_vistos)
    except ExercicioInvalido as e:
        raise TreinoIndisponivel(
            "Não consegui montar um exercício bom agora. Tente de novo.") from e

    exercicio = ExercicioGerado(
        student_id=student.id,
        error_category=alvo["error_category"],
        titulo=dados["titulo"],
        enunciado=dados["enunciado"],
        casos_teste=dados["casos_teste"],
        required_structures=dados["required_structures"],
    )
    db.add(exercicio)
    db.commit()
    db.refresh(exercicio)
    return _exercicio_detalhe(exercicio, db)


# ── treino ───────────────────────────────────────────────────────────────────

def _meu_exercicio(student: Student, exercicio_id: int, db: Session) -> ExercicioGerado:
    exercicio = db.get(ExercicioGerado, exercicio_id)
    if not exercicio or exercicio.student_id != student.id:
        raise ValueError("Exercício não encontrado.")
    return exercicio


def detalhe(student: Student, exercicio_id: int, db: Session) -> dict:
    return _exercicio_detalhe(_meu_exercicio(student, exercicio_id, db), db)


def treinar(student: Student, exercicio_id: int, code: str, db: Session) -> dict:
    """Submete contra um exercício gerado. Sem janela e sem teto: é treino."""
    exercicio = _meu_exercicio(student, exercicio_id, db)
    if exercicio.reportado:
        raise ValueError("Este exercício foi reportado e saiu da trilha.")

    anteriores = (
        db.query(TentativaDeTreino)
        .filter(TentativaDeTreino.exercicio_id == exercicio.id)
        .order_by(TentativaDeTreino.attempt_number)
        .all()
    )
    resultado = evaluate_code(
        code,
        [{"input": c.get("input", ""), "expected_output": c.get("expected_output", "")}
         for c in (exercicio.casos_teste or [])],
        exercicio.required_structures or [],
        [],
        [],
    )
    diagnostico = resultado.get("diagnosis") or {}
    tentativa = TentativaDeTreino(
        exercicio_id=exercicio.id,
        student_id=student.id,
        code=code,
        compile_error=resultado.get("compile_error") or "",
        warnings=resultado.get("warnings") or "",
        all_tests_passed=resultado.get("all_tests_passed"),
        error_category=diagnostico.get("error_category") or "",
        pedagogical_diagnosis=diagnostico.get("pedagogical_diagnosis") or "",
        actionable_feedback=diagnostico.get("actionable_feedback") or "",
        test_results=resultado.get("test_results") or [],
        attempt_number=len(anteriores) + 1,
    )
    db.add(tentativa)
    if resultado.get("all_tests_passed"):
        exercicio.resolvido = True
    db.commit()
    db.refresh(tentativa)

    return {
        "tentativa": _tentativa_dict(tentativa),
        "tentativas": len(anteriores) + 1,
        "resolvido": bool(exercicio.resolvido),
        "structure_check": resultado.get("structure_check"),
    }


def reportar(student: Student, exercicio_id: int, motivo: str, db: Session) -> dict:
    """Sem fila de revisão, o aluno é o controle de qualidade. Reportado sai da
    trilha e deixa de contar, mas fica gravado com o motivo: é isso que diz
    depois se a geração está boa o bastante."""
    exercicio = _meu_exercicio(student, exercicio_id, db)
    exercicio.reportado = True
    exercicio.reportado_motivo = (motivo or "").strip()[:500] or None
    db.commit()
    return {"exercicio_id": exercicio.id, "reportado": True}


# ── serialização ─────────────────────────────────────────────────────────────

def _iso(valor) -> str | None:
    return valor.isoformat() if valor else None


def _exercicio_resumo(e: ExercicioGerado) -> dict:
    return {
        "id": e.id,
        "titulo": e.titulo,
        "error_category": e.error_category,
        "resolvido": bool(e.resolvido),
        "tentativas": len(e.tentativas),
        "created_at": _iso(e.created_at) or "",
    }


def _exercicio_detalhe(e: ExercicioGerado, db: Session, reaproveitado: bool = False) -> dict:
    tentativas = sorted(e.tentativas, key=lambda t: t.attempt_number, reverse=True)
    return {
        **_exercicio_resumo(e),
        "enunciado": e.enunciado,
        "required_structures": e.required_structures or [],
        "total_testes": len(e.casos_teste or []),
        "reaproveitado": reaproveitado,
        "tentativas_lista": [_tentativa_dict(t) for t in tentativas],
    }


def _tentativa_dict(t: TentativaDeTreino) -> dict:
    resultados = t.test_results or []
    return {
        "id": t.id,
        "attempt_number": t.attempt_number or 1,
        "code": t.code or "",
        "all_tests_passed": t.all_tests_passed,
        "compile_error": t.compile_error or "",
        "warnings": t.warnings or "",
        "error_category": t.error_category or "",
        "pedagogical_diagnosis": t.pedagogical_diagnosis or "",
        "actionable_feedback": t.actionable_feedback or "",
        "submitted_at": _iso(t.submitted_at) or "",
        "tests_passed": sum(1 for r in resultados if r.get("passed")),
        "tests_total": len(resultados),
        "test_results": [
            {
                "input": r.get("input", ""),
                "expected_output": r.get("expected_output", ""),
                "actual_output": r.get("actual_output", ""),
                "passed": bool(r.get("passed")),
            }
            for r in resultados
        ],
    }
