import secrets
import string
from collections import Counter, defaultdict

# UNIFEI: aprovado é quem obtém pelo menos 60% da prova (por NOTA).
APPROVAL_THRESHOLD = 0.60
# Variação em pontos percentuais a partir da qual a dificuldade mudou de
# verdade entre a primeira e a última prova. Abaixo disso é ruído da amostra.
VARIACAO_RELEVANTE = 5.0
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.orm import Exam, Question, Submission, Turma

# Alfabeto sem caracteres ambíguos (O/0, I/1), porque o código é ditado em sala.
_ALFABETO_CODIGO = ''.join(c for c in string.ascii_uppercase + string.digits if c not in 'O0I1')
_TAMANHO_CODIGO = 6


def gerar_codigo_acesso(db: Session) -> str:
    """Código de entrada do aluno na turma, único no banco."""
    while True:
        codigo = ''.join(secrets.choice(_ALFABETO_CODIGO) for _ in range(_TAMANHO_CODIGO))
        if not db.query(Turma).filter(Turma.codigo_acesso == codigo).first():
            return codigo


def create_turma(nome: str, codigo: str, db: Session, professor_id: int | None = None) -> Turma:
    turma = Turma(
        nome=nome,
        codigo=codigo,
        codigo_acesso=gerar_codigo_acesso(db),
        created_at=datetime.utcnow(),
        professor_id=professor_id,
    )
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
            "codigo_acesso": t.codigo_acesso,
            "created_at": t.created_at.isoformat(),
            "exam_count": len(t.exams),
            "aluno_count": len(t.enrollments),
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
            "titulo": exam.titulo,
            "publicada": bool(exam.publicada),
            "created_at": exam.created_at.isoformat(),
            "question_count": len(exam.questions),
            "submission_count": submission_count,
            "modo": exam.modo or "prova",
        })
    return {
        "id": turma.id,
        "nome": turma.nome,
        "codigo": turma.codigo,
        "codigo_acesso": turma.codigo_acesso,
        "created_at": turma.created_at.isoformat(),
        "aluno_count": len(turma.enrollments),
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
    erros_por_prova: list[tuple] = []

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

        erros_da_prova = Counter(
            s.error_category for s in exam_subs
            if s.error_category and s.error_category != "Correto"
        )
        provas.append({
            "id": exam.id,
            "filename": exam.filename,
            "titulo": exam.titulo,
            "created_at": exam.created_at.isoformat(),
            "pass_rate": round(pass_rate, 1) if pass_rate is not None else None,
            "total_submissoes": len(exam_subs),
            "total_alunos": total_alunos_exam,
            "top_erros": [
                {"error_category": cat, "count": cnt}
                for cat, cnt in erros_da_prova.most_common(5)
            ],
        })
        erros_por_prova.append((exam, exam_subs, erros_da_prova))

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
        "trajetoria": _trajetoria_de_erros(erros_por_prova),
    }


def _trajetoria_de_erros(erros_por_prova: list[tuple]) -> list[dict]:
    """A dificuldade que atravessa a turma de uma prova para a outra.

    `top_erros` soma tudo e responde qual erro é o mais comum da turma. Isso
    aqui responde outra coisa: se ele está caindo ou voltando ao longo do
    semestre. Só entram categorias presentes em duas ou mais provas, porque com
    uma só não existe trajetória.

    A comparação é por proporção, não por contagem: prova com mais envios teria
    mais ocorrências de tudo, e o número cresceria sem a dificuldade ter crescido."""
    series: dict[str, list[dict]] = defaultdict(list)

    for exam, exam_subs, erros in erros_por_prova:
        com_erro = sum(erros.values())
        if not com_erro:
            continue
        for categoria, ocorrencias in erros.items():
            alunos = len({
                s.matricula for s in exam_subs
                if s.error_category == categoria and s.matricula
            })
            series[categoria].append({
                "exam_id": exam.id,
                "titulo": exam.titulo or exam.filename or f"Atividade {exam.id}",
                "ocorrencias": ocorrencias,
                "alunos": alunos,
                "proporcao": round(ocorrencias / com_erro * 100, 1),
            })

    trajetoria = []
    for categoria, pontos in series.items():
        if len(pontos) < 2:
            continue
        delta = pontos[-1]["proporcao"] - pontos[0]["proporcao"]
        if delta >= VARIACAO_RELEVANTE:
            tendencia = "subindo"
        elif delta <= -VARIACAO_RELEVANTE:
            tendencia = "caindo"
        else:
            tendencia = "estavel"
        trajetoria.append({
            "error_category": categoria,
            "provas": len(pontos),
            "total": sum(p["ocorrencias"] for p in pontos),
            "tendencia": tendencia,
            "pontos": pontos,
        })

    trajetoria.sort(key=lambda t: (-t["provas"], -t["total"]))
    return trajetoria
