from collections import Counter, defaultdict

# UNIFEI: aprovado é quem obtém pelo menos 60% da prova (por NOTA).
APPROVAL_THRESHOLD = 0.60
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.orm import Exam, Question, Submission, Turma


def create_turma(nome: str, codigo: str, db: Session, professor_id: int | None = None) -> Turma:
    turma = Turma(nome=nome, codigo=codigo, created_at=datetime.utcnow(), professor_id=professor_id)
    db.add(turma)
    db.commit()
    db.refresh(turma)
    return turma


def update_turma(turma: Turma, nome: str, codigo: str, db: Session) -> Turma:
    turma.nome = nome
    turma.codigo = codigo
    db.commit()
    db.refresh(turma)
    return turma


def delete_turma(turma: Turma, db: Session) -> None:
    """Exclusão em cascata total: remove cada prova (e tudo abaixo) e a turma."""
    from app.services.exam_service import delete_exam
    for exam in list(turma.exams):
        delete_exam(exam, db)
    db.delete(turma)
    db.commit()


def list_turmas(db: Session, professor_id: int | None = None) -> list:
    q = db.query(Turma)
    if professor_id is not None:
        q = q.filter(Turma.professor_id == professor_id)
    turmas = q.order_by(Turma.created_at.desc()).all()
    return [
        {
            "id": t.id,
            "nome": t.nome,
            "codigo": t.codigo,
            "created_at": t.created_at.isoformat(),
            "exam_count": len(t.exams),
        }
        for t in turmas
    ]


def get_turma_detail(turma_id: int, db: Session, professor_id: int | None = None) -> dict | None:
    q = db.query(Turma).filter(Turma.id == turma_id)
    if professor_id is not None:
        q = q.filter(Turma.professor_id == professor_id)
    turma = q.first()
    if not turma:
        return None
    exams = []
    for exam in turma.exams:
        submission_count = sum(len(q2.submissions) for q2 in exam.questions)
        exams.append({
            "id": exam.id,
            "filename": exam.filename,
            "created_at": exam.created_at.isoformat(),
            "question_count": len(exam.questions),
            "submission_count": submission_count,
        })
    return {
        "id": turma.id,
        "nome": turma.nome,
        "codigo": turma.codigo,
        "created_at": turma.created_at.isoformat(),
        "exams": exams,
    }


def get_turma_analytics(turma_id: int, db: Session, professor_id: int | None = None) -> dict | None:
    q = db.query(Turma).filter(Turma.id == turma_id)
    if professor_id is not None:
        q = q.filter(Turma.professor_id == professor_id)
    turma = q.first()
    if not turma:
        return None

    all_submissions: list[Submission] = []
    provas = []
    pass_rates = []

    for exam in sorted(turma.exams, key=lambda e: e.created_at):
        exam_subs: list[Submission] = []
        # Nota da prova por aluno = soma ponderada das questões pelo VALOR de cada
        # uma (Question.points); dentro da questão, a fração de casos de teste que
        # passam (crédito parcial), tomando a MELHOR submissão do aluno por questão.
        # Questão não respondida conta 0. Aprovado = nota >= 60% do total da prova.
        total_points = 0.0
        q_points: dict[int, float] = {}
        best_q_score: dict[tuple[str, int], float] = defaultdict(float)
        alunos_exam: set[str] = set()
        for question in exam.questions:
            pts = question.points if question.points is not None else 1.0
            q_points[question.id] = pts
            total_points += pts
            exam_subs.extend(question.submissions)
            for s in question.submissions:
                if not s.matricula:
                    continue
                alunos_exam.add(s.matricula)
                if s.compile_error or not s.test_results:
                    frac = 0.0
                else:
                    frac = sum(1 for tr in s.test_results if tr.passed) / len(s.test_results)
                key = (s.matricula, question.id)
                if frac > best_q_score[key]:
                    best_q_score[key] = frac

        all_submissions.extend(exam_subs)

        grade = defaultdict(float)
        for (matricula, qid), frac in best_q_score.items():
            grade[matricula] += frac * q_points[qid]
        passed_alunos = {
            m for m in alunos_exam
            if total_points > 0 and grade[m] / total_points >= APPROVAL_THRESHOLD
        }

        total_alunos_exam = len(alunos_exam)
        pass_rate = (len(passed_alunos) / total_alunos_exam * 100) if total_alunos_exam > 0 else None
        if pass_rate is not None:
            pass_rates.append(pass_rate)

        provas.append({
            "id": exam.id,
            "filename": exam.filename,
            "created_at": exam.created_at.isoformat(),
            "pass_rate": round(pass_rate, 1) if pass_rate is not None else None,
            "total_submissoes": len(exam_subs),
            "total_alunos": total_alunos_exam,
        })

    total_alunos = len({s.matricula for s in all_submissions if s.matricula})
    total_submissoes = len(all_submissions)
    aproveitamento_medio = round(sum(pass_rates) / len(pass_rates), 1) if pass_rates else None

    error_counter = Counter(
        s.error_category for s in all_submissions
        if s.error_category and s.error_category != "Correto"
    )
    top_erros = [
        {"error_category": cat, "count": cnt}
        for cat, cnt in error_counter.most_common(5)
    ]

    return {
        "turma_id": turma_id,
        "total_alunos": total_alunos,
        "aproveitamento_medio": aproveitamento_medio,
        "total_submissoes": total_submissoes,
        "provas": provas,
        "top_erros": top_erros,
    }
