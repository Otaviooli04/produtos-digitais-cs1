"""Atividades sob a ótica do aluno: o que ele pode resolver, o que já tentou e o
que a série de tentativas diz sobre a evolução dele.

Duas regras sustentam este módulo:
- toda tentativa é gravada (nunca só a final), porque é o histórico que permite
  acompanhar evolução e detectar quem travou;
- disponibilidade é regra de dado, não de modo: janela e teto de tentativas valem
  sempre que estiverem preenchidos. `modo` diz ao aluno o que a atividade é
  (treino ou prova) e define os padrões que o professor vê ao criá-la.
"""
import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.engine.evaluators.code_evaluator import evaluate_code
from app.models.orm import Exam, Question, Student, Submission
from app.services.calendario import situacao_da_atividade
from app.services.historico_do_aluno import (
    CATEGORIA_CORRETA, ERRO, FALHA, LISTA, TRILHA, dias_seguidos, erros_do_aluno, evolucao,
    ler_historico, resolucoes, rotulos, superados, tendencias,
)

logger = logging.getLogger(__name__)


class AtividadeIndisponivel(Exception):
    """A atividade existe para este aluno, mas as regras dela barram a submissão."""


# ── consultas de apoio ───────────────────────────────────────────────────────

def _turma_ids(student: Student) -> list[int]:
    return [e.turma_id for e in student.enrollments]


def _tentativas_por_questao(student: Student, db: Session,
                            question_ids: list[int]) -> dict[int, list[Submission]]:
    """Tentativas do aluno agrupadas por questão, em ordem cronológica."""
    if not question_ids:
        return {}
    subs = (
        db.query(Submission)
        .filter(
            Submission.student_id == student.id,
            Submission.question_id.in_(question_ids),
        )
        .order_by(Submission.attempt_number, Submission.id)
        .all()
    )
    mapa: dict[int, list[Submission]] = defaultdict(list)
    for s in subs:
        mapa[s.question_id].append(s)
    return mapa


def _resolvida(tentativas: list[Submission]) -> bool:
    return any(s.error_category == CATEGORIA_CORRETA for s in tentativas)


def _questoes_ordenadas(exam: Exam) -> list[Question]:
    def chave(q):
        try:
            return (0, int(q.number))
        except (TypeError, ValueError):
            return (1, q.number or "")
    return sorted(exam.questions, key=chave)


def _testes(sub: Submission) -> tuple[int, int]:
    return sum(1 for tr in sub.test_results if tr.passed), len(sub.test_results)


def _restantes(exam: Exam, usadas: int) -> int | None:
    if exam.max_tentativas is None:
        return None
    return max(0, exam.max_tentativas - usadas)


def _iso(valor) -> str | None:
    return valor.isoformat() if valor else None


def _atividade_do_aluno(student: Student, exam_id: int, db: Session) -> Exam:
    """Só existe atividade para o aluno dentro de turma em que ele entrou."""
    turma_ids = _turma_ids(student)
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam or exam.turma_id not in turma_ids or not exam.publicada:
        raise ValueError("Atividade não encontrada.")
    return exam


def titulo_da_atividade(exam: Exam) -> str:
    """O nome que o aluno lê. O arquivo é só a origem, e serve de reserva
    enquanto o professor não dá um nome à atividade."""
    return exam.titulo or exam.filename or f"Atividade {exam.id}"


# ── lista e detalhe ──────────────────────────────────────────────────────────

def listar_atividades(student: Student, db: Session, turma_id: int | None = None) -> list[dict]:
    turma_ids = _turma_ids(student)
    if turma_id is not None:
        if turma_id not in turma_ids:
            raise ValueError("Turma não encontrada.")
        turma_ids = [turma_id]
    if not turma_ids:
        return []

    exams = (
        db.query(Exam)
        .filter(Exam.turma_id.in_(turma_ids), Exam.publicada.is_(True))
        .order_by(Exam.created_at.desc())
        .all()
    )
    question_ids = [q.id for e in exams for q in e.questions]
    mapa = _tentativas_por_questao(student, db, question_ids)
    return [_resumo(exam, mapa) for exam in exams]


def _resumo(exam: Exam, mapa: dict[int, list[Submission]]) -> dict:
    questoes = _questoes_ordenadas(exam)
    tentativas = sum(len(mapa.get(q.id, [])) for q in questoes)
    resolvidas = sum(1 for q in questoes if _resolvida(mapa.get(q.id, [])))
    situacao = situacao_da_atividade(exam)
    return {
        "exam_id": exam.id,
        "titulo": titulo_da_atividade(exam),
        "turma_id": exam.turma_id,
        "turma_nome": exam.turma.nome if exam.turma else "",
        "modo": exam.modo or Exam.MODO_PROVA,
        "abre_em": _iso(exam.abre_em),
        "fecha_em": _iso(exam.fecha_em),
        "max_tentativas": exam.max_tentativas,
        "aberta": situacao == "aberta",
        "situacao": situacao,
        "total_questoes": len(questoes),
        "questoes_resolvidas": resolvidas,
        "tentativas": tentativas,
    }


def detalhe_atividade(student: Student, exam_id: int, db: Session) -> dict:
    exam = _atividade_do_aluno(student, exam_id, db)
    questoes = _questoes_ordenadas(exam)
    mapa = _tentativas_por_questao(student, db, [q.id for q in questoes])

    detalhe = _resumo(exam, mapa)
    detalhe["questoes"] = [_questao_com_status(q, exam, mapa.get(q.id, [])) for q in questoes]
    return detalhe


def _questao_com_status(question: Question, exam: Exam, tentativas: list[Submission]) -> dict:
    melhor_passados, total_testes = 0, len(question.test_cases)
    for sub in tentativas:
        passados, total = _testes(sub)
        if total and passados > melhor_passados:
            melhor_passados = passados
    ultima = tentativas[-1] if tentativas else None
    return {
        "id": question.id,
        "number": question.number,
        "statement": question.statement or "",
        "points": question.points if question.points is not None else 1.0,
        "required_structures": question.required_structures or [],
        "forbidden_structures": question.forbidden_structures or [],
        "requires_loop": bool(question.requires_loop),
        "required_functions": question.required_functions or [],
        "tentativas": len(tentativas),
        "resolvida": _resolvida(tentativas),
        "tentativas_restantes": _restantes(exam, len(tentativas)),
        "melhor_testes_passados": melhor_passados,
        "testes_totais": total_testes,
        "ultima_categoria": ultima.error_category if ultima else None,
        "ultimo_codigo": ultima.code if ultima else None,
    }


# ── submissão ────────────────────────────────────────────────────────────────

def submeter(student: Student, exam_id: int, question_number: str, code: str,
             db: Session) -> dict:
    exam = _atividade_do_aluno(student, exam_id, db)
    situacao = situacao_da_atividade(exam)
    if situacao == "agendada":
        raise AtividadeIndisponivel("Esta atividade ainda não abriu.")
    if situacao == "encerrada":
        raise AtividadeIndisponivel("Esta atividade já encerrou.")

    question = next((q for q in exam.questions if q.number == question_number), None)
    if not question:
        raise ValueError(f"Questão {question_number} não encontrada nesta atividade.")

    if exam.max_tentativas is not None:
        # Dois envios ao mesmo tempo contariam as mesmas tentativas e passariam
        # juntos do teto. A trava na linha do aluno enfileira os envios dele até
        # o primeiro gravar, o que inclui a correção no Docker (segundos). NO KEY
        # não bloqueia quem só referencia o aluno (acessos, matrícula), mas um
        # UPDATE futuro na linha de Student esperaria a correção terminar.
        db.query(Student).filter(Student.id == student.id).with_for_update(key_share=True).one()
    anteriores = _tentativas_por_questao(student, db, [question.id]).get(question.id, [])
    if exam.max_tentativas is not None and len(anteriores) >= exam.max_tentativas:
        raise AtividadeIndisponivel(
            f"Você já usou as {exam.max_tentativas} tentativas desta questão.")

    from app.services.submission_service import persist_submission

    result = evaluate_code(
        code,
        [{"input": tc.input, "expected_output": tc.expected_output} for tc in question.test_cases],
        question.required_structures or [],
        question.forbidden_structures or [],
        question.required_functions or [],
    )
    submissao = persist_submission(
        question, code, result, db,
        matricula=student.matricula,
        student_id=student.id,
        attempt_number=len(anteriores) + 1,
    )

    _agrupar_em_silencio(question.id, db)

    usadas = len(anteriores) + 1
    return {
        "tentativa": tentativa_to_dict(submissao, db, com_resposta=True),
        "tentativas": usadas,
        "tentativas_restantes": _restantes(exam, usadas),
        "resolvida": _resolvida(anteriores + [submissao]),
        "structure_check": result.get("structure_check"),
        "function_check": result.get("function_check"),
    }


def _agrupar_em_silencio(question_id: int, db: Session) -> None:
    """Refaz o agrupamento da questão a cada envio.

    É o mesmo agrupamento de sempre, o do TCC, e a única mudança é a frequência:
    antes só rodava no fim do lote ou no botão do professor, e no fluxo real da
    turma, em que o aluno envia um a um, nenhum dos dois disparava.

    Falha aqui nunca pode derrubar a submissão: o aluno já recebeu o diagnóstico
    dele, que é o que importa nesta requisição."""
    try:
        from app.ml.cluster import cluster_question
        cluster_question(question_id, db)
    except Exception:  # noqa: BLE001 — agrupamento é secundário à resposta do aluno
        logger.exception("Falha ao agrupar a questão %s após o envio", question_id)
        db.rollback()


def resposta_do_grupo(sub: Submission, db: Session) -> tuple[str | None, str | None]:
    """O retorno que o professor escreveu para o grupo desta tentativa.

    O aluno nunca vê que está em um grupo, nem quem mais está nele. Ele vê um
    retorno do professor dele, porque é o que é: dizer ao aluno que a resposta
    foi escrita para um grupo seria dizer que ela não é dele."""
    from app.models.orm import QuestionCluster

    if sub.cluster_id is None:
        return None, None
    grupo = db.query(QuestionCluster).filter(
        QuestionCluster.question_id == sub.question_id,
        QuestionCluster.cluster_label == sub.cluster_id,
    ).first()
    if not grupo or not grupo.resposta_professor:
        return None, None
    return grupo.resposta_professor, _iso(grupo.resposta_em)


def tentativa_to_dict(sub: Submission, db: Session | None = None,
                      com_resposta: bool = False) -> dict:
    passados, total = _testes(sub)
    resposta, resposta_em = (
        resposta_do_grupo(sub, db) if (com_resposta and db is not None) else (None, None))
    return {
        "submission_id": sub.id,
        "attempt_number": sub.attempt_number or 1,
        "code": sub.code or "",
        "all_tests_passed": sub.all_tests_passed,
        "compile_error": sub.compile_error or "",
        "warnings": sub.warnings or "",
        "error_category": sub.error_category or "",
        "pedagogical_diagnosis": sub.pedagogical_diagnosis or "",
        "actionable_feedback": sub.actionable_feedback or "",
        "submitted_at": _iso(sub.submitted_at) or "",
        "tests_passed": passados,
        "tests_total": total,
        "explicacao": sub.llm_explanation or None,
        "test_results": [
            {
                "input": tr.input or "",
                "expected_output": tr.expected_output or "",
                "actual_output": tr.actual_output or "",
                "passed": bool(tr.passed),
            }
            for tr in sub.test_results
        ],
        "resposta_do_professor": resposta,
        "resposta_do_professor_em": resposta_em,
    }


# ── histórico ────────────────────────────────────────────────────────────────

def historico_questao(student: Student, exam_id: int, question_number: str,
                      db: Session) -> dict:
    exam = _atividade_do_aluno(student, exam_id, db)
    question = next((q for q in exam.questions if q.number == question_number), None)
    if not question:
        raise ValueError(f"Questão {question_number} não encontrada nesta atividade.")

    tentativas = _tentativas_por_questao(student, db, [question.id]).get(question.id, [])
    return {
        "question_number": question.number,
        "statement": question.statement or "",
        "resolvida": _resolvida(tentativas),
        # Mais recente primeiro: é o que o aluno quer ver ao abrir a tela. Só ela
        # carrega o retorno do professor, senão o mesmo texto apareceria repetido
        # em toda tentativa antiga que caiu no mesmo grupo.
        "tentativas": [
            tentativa_to_dict(s, db, com_resposta=(i == 0))
            for i, s in enumerate(reversed(tentativas))
        ],
    }


# ── explicação individual ────────────────────────────────────────────────────

def explicar_tentativa(student: Student, submission_id: int, db: Session) -> dict:
    """Explicação em linguagem natural da tentativa do aluno, gerada sob demanda.

    O diagnóstico das heurísticas continua sendo a fonte da verdade — a LLM só
    traduz o erro para quem o cometeu. Uma geração por tentativa, cacheada, e
    nunca para tentativa correta (não há erro a explicar e a chamada seria custo
    puro)."""
    sub = (
        db.query(Submission)
        .filter(Submission.id == submission_id, Submission.student_id == student.id)
        .first()
    )
    if not sub:
        raise ValueError("Tentativa não encontrada.")
    if sub.error_category == CATEGORIA_CORRETA:
        raise AtividadeIndisponivel("Esta tentativa está correta, não há erro a explicar.")
    if sub.llm_explanation:
        return {"explicacao": sub.llm_explanation, "gerada_agora": False}

    from app.llm.student_explainer import generate_student_explanation

    texto = generate_student_explanation(
        statement=(sub.question.statement if sub.question else ""),
        code=sub.code or "",
        error_category=sub.error_category or "",
        pedagogical_diagnosis=sub.pedagogical_diagnosis or "",
        test_results=[
            {
                "input": tr.input,
                "expected_output": tr.expected_output,
                "actual_output": tr.actual_output,
                "passed": tr.passed,
            }
            for tr in sub.test_results
        ],
    )
    if not texto:
        raise RuntimeError("Não foi possível gerar a explicação agora. Tente de novo.")

    sub.llm_explanation = texto
    db.commit()
    return {"explicacao": texto, "gerada_agora": True}


# ── progresso ────────────────────────────────────────────────────────────────

def progresso(student: Student, db: Session) -> dict:
    """Os números do aluno contra a turma, com o treino somado no esforço.

    Questões resolvidas e atividades concluídas são só da turma, porque o total
    é o da turma. Tentativas, acertos de primeira, dias seguidos e a evolução
    juntam as questões e os exercícios da trilha."""
    turma_ids = _turma_ids(student)
    exams = db.query(Exam).filter(
        Exam.turma_id.in_(turma_ids), Exam.publicada.is_(True)
    ).all() if turma_ids else []
    questoes = [q for e in exams for q in e.questions]
    ids_das_questoes = {q.id for q in questoes}

    envios = [
        e for e in ler_historico(student, db)
        if e.origem == TRILHA or e.item_id in ids_das_questoes
    ]
    resolvidas = resolucoes(envios)
    questoes_resolvidas = {r.item[1] for r in resolvidas if r.item[0] == LISTA}
    concluidas = sum(
        1 for e in exams
        if e.questions and all(q.id in questoes_resolvidas for q in e.questions)
    )

    return {
        "total_atividades": len(exams),
        "atividades_concluidas": concluidas,
        "total_questoes": len(questoes),
        "questoes_resolvidas": len(questoes_resolvidas),
        "total_tentativas": len(envios),
        "tentativas_no_treino": sum(1 for e in envios if e.origem == TRILHA),
        "exercicios_resolvidos": sum(1 for r in resolvidas if r.item[0] == TRILHA),
        "tentativas_por_questao_resolvida": (
            round(sum(r.tentativas for r in resolvidas) / len(resolvidas), 1)
            if resolvidas else None
        ),
        "acertos_de_primeira": sum(1 for r in resolvidas if r.tentativas == 1),
        "dias_seguidos": dias_seguidos(envios, datetime.utcnow().date()),
        "ultima_submissao": _iso(envios[-1].momento) if envios else None,
        "evolucao": evolucao(envios, resolvidas),
    }


# ── erros recorrentes ────────────────────────────────────────────────────────

def erros_recorrentes(student: Student, db: Session) -> dict:
    """O padrão que o aluno repete, que é justamente o que ele não enxerga sozinho.
    Junta as listas e a trilha, e separa o que ele já superou treinando.
    Determinístico: sai das categorias das heurísticas, sem chamada de LLM."""
    turma_ids = _turma_ids(student)
    exams = db.query(Exam).filter(
        Exam.turma_id.in_(turma_ids), Exam.publicada.is_(True)
    ).all() if turma_ids else []
    rotulo_questao = {
        q.id: f"{titulo_da_atividade(e)} · Q{q.number}"
        for e in exams for q in e.questions
    }

    envios = ler_historico(student, db)
    erros = erros_do_aluno(envios)
    tendencia = tendencias(envios)

    return {
        "total_submissoes": sum(1 for e in envios if e.resultado != FALHA),
        "total_com_erro": sum(1 for e in envios if e.resultado == ERRO),
        "erros": [
            {
                "error_category": erro.categoria,
                "total": erro.total,
                "no_treino": erro.no_treino,
                "recentes": tendencia[erro.categoria].recentes,
                "anteriores": tendencia[erro.categoria].anteriores,
                "tendencia": tendencia[erro.categoria].sentido,
                "questoes": rotulos(erro, rotulo_questao),
                "ultima_ocorrencia": _iso(erro.ultima_ocorrencia) or "",
                "o_que_fazer": erro.o_que_fazer,
            }
            for erro in erros if erro.ativo
        ],
        "superados": superados(erros),
    }
