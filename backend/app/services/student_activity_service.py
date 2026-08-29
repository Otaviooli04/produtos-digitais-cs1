"""Atividades sob a ótica do aluno: o que ele pode resolver, o que já tentou e o
que a série de tentativas diz sobre a evolução dele.

Duas regras sustentam este módulo:
- toda tentativa é gravada (nunca só a final), porque é o histórico que permite
  acompanhar evolução e detectar quem travou;
- disponibilidade é regra de dado, não de modo: janela e teto de tentativas valem
  sempre que estiverem preenchidos. `modo` diz ao aluno o que a atividade é
  (treino ou prova) e define os padrões que o professor vê ao criá-la.
"""
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.engine.evaluators.code_evaluator import evaluate_code
from app.models.orm import Exam, Question, Student, Submission

CATEGORIA_CORRETA = "Correto"
# Quantas submissões contam como "recentes" ao medir a tendência de um erro.
JANELA_RECENTE = 10


class AtividadeIndisponivel(Exception):
    """A atividade existe para este aluno, mas as regras dela barram a submissão."""


# ── consultas de apoio ───────────────────────────────────────────────────────

def _turma_ids(student: Student) -> list[int]:
    return [e.turma_id for e in student.enrollments]


def _situacao(exam: Exam, agora: datetime | None = None) -> str:
    agora = agora or datetime.utcnow()
    if exam.abre_em and agora < exam.abre_em:
        return "agendada"
    if exam.fecha_em and agora > exam.fecha_em:
        return "encerrada"
    return "aberta"


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
    if not exam or exam.turma_id not in turma_ids:
        raise ValueError("Atividade não encontrada.")
    return exam


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
        .filter(Exam.turma_id.in_(turma_ids))
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
    situacao = _situacao(exam)
    return {
        "exam_id": exam.id,
        "titulo": exam.filename or f"Atividade {exam.id}",
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
    situacao = _situacao(exam)
    if situacao == "agendada":
        raise AtividadeIndisponivel("Esta atividade ainda não abriu.")
    if situacao == "encerrada":
        raise AtividadeIndisponivel("Esta atividade já encerrou.")

    question = next((q for q in exam.questions if q.number == question_number), None)
    if not question:
        raise ValueError(f"Questão {question_number} não encontrada nesta atividade.")

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

    usadas = len(anteriores) + 1
    return {
        "tentativa": tentativa_to_dict(submissao),
        "tentativas": usadas,
        "tentativas_restantes": _restantes(exam, usadas),
        "resolvida": _resolvida(anteriores + [submissao]),
        "structure_check": result.get("structure_check"),
        "function_check": result.get("function_check"),
    }


def tentativa_to_dict(sub: Submission) -> dict:
    passados, total = _testes(sub)
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
        # Mais recente primeiro: é o que o aluno quer ver ao abrir a tela.
        "tentativas": [tentativa_to_dict(s) for s in reversed(tentativas)],
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
    turma_ids = _turma_ids(student)
    exams = (
        db.query(Exam).filter(Exam.turma_id.in_(turma_ids)).all() if turma_ids else []
    )
    questoes = [q for e in exams for q in e.questions]
    mapa = _tentativas_por_questao(student, db, [q.id for q in questoes])

    todas = [s for lista in mapa.values() for s in lista]
    resolvidas = [q for q in questoes if _resolvida(mapa.get(q.id, []))]

    tentativas_ate_acertar = []
    acertos_de_primeira = 0
    for q in resolvidas:
        primeira_correta = next(
            s for s in mapa[q.id] if s.error_category == CATEGORIA_CORRETA)
        n = primeira_correta.attempt_number or 1
        tentativas_ate_acertar.append(n)
        if n == 1:
            acertos_de_primeira += 1

    concluidas = sum(
        1 for e in exams
        if e.questions and all(_resolvida(mapa.get(q.id, [])) for q in e.questions)
    )
    ultima = max((s.submitted_at for s in todas if s.submitted_at), default=None)

    return {
        "total_atividades": len(exams),
        "atividades_concluidas": concluidas,
        "total_questoes": len(questoes),
        "questoes_resolvidas": len(resolvidas),
        "total_tentativas": len(todas),
        "tentativas_por_questao_resolvida": (
            round(sum(tentativas_ate_acertar) / len(tentativas_ate_acertar), 1)
            if tentativas_ate_acertar else None
        ),
        "acertos_de_primeira": acertos_de_primeira,
        "dias_seguidos": _dias_seguidos(todas),
        "ultima_submissao": _iso(ultima),
        "evolucao": _evolucao(mapa, questoes),
    }


def _dias_seguidos(submissoes: list[Submission]) -> int:
    """Sequência de dias consecutivos com pelo menos uma submissão, terminando
    hoje ou ontem (quem submeteu ontem ainda não perdeu a sequência)."""
    dias = {s.submitted_at.date() for s in submissoes if s.submitted_at}
    if not dias:
        return 0
    hoje = datetime.utcnow().date()
    referencia = hoje if hoje in dias else hoje - timedelta(days=1)
    if referencia not in dias:
        return 0
    sequencia = 0
    while referencia in dias:
        sequencia += 1
        referencia -= timedelta(days=1)
    return sequencia


def _evolucao(mapa: dict[int, list[Submission]], questoes: list[Question]) -> list[dict]:
    """Série semanal de tentativas e de questões resolvidas pela primeira vez."""
    tentativas_por_semana: dict[str, int] = defaultdict(int)
    resolvidas_por_semana: dict[str, int] = defaultdict(int)

    for q in questoes:
        for sub in mapa.get(q.id, []):
            if not sub.submitted_at:
                continue
            tentativas_por_semana[_semana(sub.submitted_at)] += 1
        primeira_correta = next(
            (s for s in mapa.get(q.id, []) if s.error_category == CATEGORIA_CORRETA), None)
        if primeira_correta and primeira_correta.submitted_at:
            resolvidas_por_semana[_semana(primeira_correta.submitted_at)] += 1

    return [
        {
            "periodo": semana,
            "tentativas": tentativas_por_semana[semana],
            "resolvidas": resolvidas_por_semana.get(semana, 0),
        }
        for semana in sorted(tentativas_por_semana)
    ]


def _semana(momento: datetime) -> str:
    dia = momento.date()
    return (dia - timedelta(days=dia.weekday())).isoformat()


# ── erros recorrentes ────────────────────────────────────────────────────────

def erros_recorrentes(student: Student, db: Session) -> dict:
    """O padrão que o aluno repete, que é justamente o que ele não enxerga sozinho.
    Determinístico: sai das categorias das heurísticas, sem chamada de LLM."""
    turma_ids = _turma_ids(student)
    exams = db.query(Exam).filter(Exam.turma_id.in_(turma_ids)).all() if turma_ids else []
    rotulo_questao = {
        q.id: f"{e.filename or 'Atividade'} · Q{q.number}"
        for e in exams for q in e.questions
    }

    todas = (
        db.query(Submission)
        .filter(Submission.student_id == student.id)
        .order_by(Submission.submitted_at, Submission.id)
        .all()
    )
    com_erro = [
        s for s in todas
        if s.error_category and s.error_category != CATEGORIA_CORRETA
    ]
    recentes_ids = {s.id for s in todas[-JANELA_RECENTE:]}

    por_categoria: dict[str, list[Submission]] = defaultdict(list)
    for s in com_erro:
        por_categoria[s.error_category].append(s)

    erros = []
    for categoria, ocorrencias in por_categoria.items():
        recentes = sum(1 for s in ocorrencias if s.id in recentes_ids)
        anteriores = len(ocorrencias) - recentes
        ultima = ocorrencias[-1]
        questoes = []
        for s in reversed(ocorrencias):
            rotulo = rotulo_questao.get(s.question_id)
            if rotulo and rotulo not in questoes:
                questoes.append(rotulo)
        erros.append({
            "error_category": categoria,
            "total": len(ocorrencias),
            "recentes": recentes,
            "anteriores": anteriores,
            "tendencia": _tendencia(recentes, anteriores, len(todas)),
            "questoes": questoes[:5],
            "ultima_ocorrencia": _iso(ultima.submitted_at) or "",
            "o_que_fazer": ultima.actionable_feedback or "",
        })

    erros.sort(key=lambda e: (-e["total"], e["error_category"]))
    return {
        "total_submissoes": len(todas),
        "total_com_erro": len(com_erro),
        "erros": erros,
    }


def _tendencia(recentes: int, anteriores: int, total_submissoes: int) -> str:
    """Compara a frequência do erro nas últimas submissões com a frequência dele
    no resto do histórico. Sem histórico anterior suficiente não há tendência."""
    janela_recente = min(JANELA_RECENTE, total_submissoes)
    janela_anterior = total_submissoes - janela_recente
    if janela_anterior == 0 or janela_recente == 0:
        return "estavel"
    taxa_recente = recentes / janela_recente
    taxa_anterior = anteriores / janela_anterior
    if taxa_recente <= taxa_anterior * 0.8:
        return "melhorando"
    if taxa_recente >= taxa_anterior * 1.2:
        return "piorando"
    return "estavel"
