import re
from collections import Counter
from sqlalchemy.orm import Session
from app.engine.document_parser import parse_document
from app.engine.semantic_extractor import extract_exam_structure
from app.models.orm import (
    Exam, Question, TestCase, ProcessingJob,
    Submission, SubmissionTestResult, QuestionCluster,
)
from app.services.job_service import create_job, run_in_background, update_job


def start_exam_processing(file_bytes: bytes, filename: str, db: Session,
                          turma_id=None, professor_id=None) -> tuple[Exam, ProcessingJob]:
    """Cria a prova imediatamente (parse é rápido) e dispara a extração via Gemini
    em segundo plano. Retorna (exam, job) para o frontend acompanhar o progresso."""
    raw_text = parse_document(file_bytes, filename)

    exam = Exam(filename=filename, raw_text=raw_text, turma_id=turma_id)
    db.add(exam)
    db.commit()
    db.refresh(exam)

    job = create_job(
        db, "exam_upload", exam_id=exam.id, professor_id=professor_id,
        stage="Aguardando extração com Gemini",
    )
    exam_id = exam.id
    # PDF é enviado nativo ao Gemini (multimodal) p/ preservar o layout das tabelas.
    mime_type = "application/pdf" if filename.lower().endswith(".pdf") else None
    run_in_background(
        job.id,
        lambda bg, jid: _process_exam_job(bg, jid, exam_id, raw_text, file_bytes, mime_type),
    )
    return exam, job


def _process_exam_job(db: Session, job_id: int, exam_id: int, raw_text: str,
                      file_bytes: bytes = None, mime_type: str = None) -> None:
    update_job(db, job_id, stage="Extraindo questões e casos de teste com Gemini")
    structure = extract_exam_structure(raw_text, file_bytes=file_bytes, mime_type=mime_type)
    questions = structure.get("questions", [])
    update_job(db, job_id, total=len(questions), stage="Salvando questões")

    n_test_cases = 0
    for i, q in enumerate(questions, 1):
        question = Question(
            exam_id=exam_id,
            number=q["number"],
            statement=q["statement"],
            required_structures=q.get("required_structures", []),
            forbidden_structures=q.get("forbidden_structures", []),
            requires_loop=q.get("requires_loop", False),
            required_functions=q.get("required_functions", []),
        )
        db.add(question)
        db.flush()
        for tc in q.get("test_cases", []):
            inp, exp = tc.get("input"), tc.get("expected_output")
            if exp is None:
                continue
            db.add(TestCase(question_id=question.id,
                            input="" if inp is None else str(inp),
                            expected_output=str(exp)))
            n_test_cases += 1
        db.commit()
        update_job(db, job_id, processed=i)

    update_job(
        db, job_id, status="done", stage="Concluído",
        result={"questions": len(questions), "test_cases": n_test_cases},
        message=f"{len(questions)} questões e {n_test_cases} casos de teste extraídos.",
    )


# ── Exclusão em cascata ──────────────────────────────────────────────────────
# O grafo Prova→Questão→{TestCase, Submissão→TestResult, Cluster} não tem
# ON DELETE CASCADE no banco, então apagamos de baixo p/ cima na ordem correta.
# Clusters apontam para a submissão representativa, por isso são removidos ANTES
# das submissões.
def _delete_questions(question_ids: list[int], db: Session) -> None:
    if not question_ids:
        return
    sub_ids = [r[0] for r in db.query(Submission.id)
               .filter(Submission.question_id.in_(question_ids)).all()]
    if sub_ids:
        db.query(SubmissionTestResult).filter(
            SubmissionTestResult.submission_id.in_(sub_ids)).delete(synchronize_session=False)
    db.query(QuestionCluster).filter(
        QuestionCluster.question_id.in_(question_ids)).delete(synchronize_session=False)
    db.query(Submission).filter(
        Submission.question_id.in_(question_ids)).delete(synchronize_session=False)
    db.query(TestCase).filter(
        TestCase.question_id.in_(question_ids)).delete(synchronize_session=False)
    db.query(Question).filter(
        Question.id.in_(question_ids)).delete(synchronize_session=False)


def delete_exam(exam: Exam, db: Session) -> None:
    _delete_questions([q.id for q in exam.questions], db)
    db.query(ProcessingJob).filter(
        ProcessingJob.exam_id == exam.id).delete(synchronize_session=False)
    db.delete(exam)
    db.commit()


def update_exam(exam: Exam, db: Session, filename: str = None, turma_id=None,
                clear_turma: bool = False, modo: str = None, abre_em=None,
                fecha_em=None, max_tentativas=None, limpar: list = None) -> Exam:
    if filename is not None:
        exam.filename = filename
    if clear_turma:
        exam.turma_id = None
    elif turma_id is not None:
        exam.turma_id = turma_id
    if modo is not None:
        exam.modo = modo
    if abre_em is not None:
        exam.abre_em = abre_em
    if fecha_em is not None:
        exam.fecha_em = fecha_em
    if max_tentativas is not None:
        exam.max_tentativas = max_tentativas
    for campo in (limpar or []):
        setattr(exam, campo, None)
    db.commit()
    db.refresh(exam)
    return exam


# ── CRUD de questão ──────────────────────────────────────────────────────────
def create_question(exam_id: int, data: dict, db: Session) -> Question:
    question = Question(
        exam_id=exam_id,
        number=data["number"],
        statement=data.get("statement", ""),
        required_structures=data.get("required_structures", []),
        forbidden_structures=data.get("forbidden_structures", []),
        requires_loop=data.get("requires_loop", False),
        required_functions=data.get("required_functions", []),
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


def update_question(question: Question, data: dict, db: Session) -> Question:
    """Aplica apenas os campos enviados (data já vem com exclude_unset)."""
    for field in ("number", "statement", "points", "required_structures",
                  "forbidden_structures", "requires_loop", "required_functions"):
        if field in data and data[field] is not None:
            setattr(question, field, data[field])
    db.commit()
    db.refresh(question)
    return question


def delete_question(question: Question, db: Session) -> None:
    _delete_questions([question.id], db)
    db.commit()


def add_test_cases(question_id: int, test_cases: list[dict], db: Session) -> int:
    for tc in test_cases:
        db.add(TestCase(
            question_id=question_id,
            input=tc["input"],
            expected_output=tc["expected_output"],
        ))
    db.commit()
    return len(test_cases)


def _natural_key(s: str):
    """Ordenação natural: 'Prova-2' antes de 'Prova-10' (números comparados como
    números, não como texto). Aplica a matrículas alfanuméricas."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s or "")]


def sorted_questions(exam: Exam) -> list:
    """Questões da prova em ordem numérica (2 antes de 10; relação ORM não garante ordem)."""
    def key(q):
        try:
            return (0, int(q.number))
        except (TypeError, ValueError):
            return (1, q.number or "")
    return sorted(exam.questions, key=key)


def _compile_error_signature(text: str) -> str:
    """Reduz a saída verbosa do gcc à mensagem do primeiro erro (sem caminho/linha),
    para agrupar erros de compilação semelhantes da turma."""
    for line in text.splitlines():
        if "error:" in line:
            return " ".join(line.split("error:", 1)[1].split()).strip() or "Erro de compilação"
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:120]
    return "Erro de compilação"


def get_exam_results(exam: Exam) -> dict:
    def _add(bucket: dict, key, matricula):
        """Acumula matrículas únicas (em ordem) por chave, para mostrar 'onde aparece'."""
        lst = bucket.setdefault(key, [])
        if matricula and matricula not in lst:
            lst.append(matricula)

    questions = []
    for q in sorted_questions(exam):
        subs = q.submissions

        # Distribuição por categoria de erro + quais alunos em cada uma.
        cat_counter: Counter = Counter()
        cat_matriculas: dict = {}
        for s in subs:
            cat = s.error_category
            if cat and cat != "Correto":
                cat_counter[cat] += 1
                _add(cat_matriculas, cat, s.matricula)
        error_dist = [
            {"error_category": cat, "count": count, "matriculas": cat_matriculas.get(cat, [])}
            for cat, count in cat_counter.most_common()
        ]

        # Falha por caso de teste: agrega por (entrada, saída esperada) de quem executou.
        tc_total: Counter = Counter()
        tc_failed: Counter = Counter()
        tc_meta: dict = {}
        tc_failed_matriculas: dict = {}
        for s in subs:
            for tr in s.test_results:
                key = (tr.input or "", tr.expected_output or "")
                tc_meta.setdefault(key, key)
                tc_total[key] += 1
                if not tr.passed:
                    tc_failed[key] += 1
                    _add(tc_failed_matriculas, key, s.matricula)
        testcase_stats = sorted(
            [
                {
                    "input": key[0],
                    "expected_output": key[1],
                    "total": tc_total[key],
                    "failed": tc_failed[key],
                    "fail_rate": round(tc_failed[key] / tc_total[key] * 100) if tc_total[key] else 0,
                    "failed_matriculas": tc_failed_matriculas.get(key, []),
                }
                for key in tc_meta
            ],
            key=lambda d: (-d["fail_rate"], -d["failed"]),
        )

        # Erros de compilação mais comuns (assinatura normalizada).
        ce_counter: Counter = Counter()
        ce_matriculas: dict = {}
        for s in subs:
            if s.compile_error:
                sig = _compile_error_signature(s.compile_error)
                ce_counter[sig] += 1
                _add(ce_matriculas, sig, s.matricula)
        compile_errors = [
            {"message": msg, "count": count, "matriculas": ce_matriculas.get(msg, [])}
            for msg, count in ce_counter.most_common(5)
        ]

        passed_count = sum(1 for s in subs if s.all_tests_passed)
        # Passou em algum caso mas não em todos.
        partial_count = sum(
            1 for s in subs
            if not s.all_tests_passed and s.test_results
            and any(tr.passed for tr in s.test_results)
        )

        questions.append({
            "question_number": q.number,
            "statement": q.statement,
            "total_submissions": len(subs),
            "passed_count": passed_count,
            "partial_count": partial_count,
            "error_distribution": error_dist,
            "testcase_stats": testcase_stats,
            "compile_errors": compile_errors,
            "submissions": [
                {
                    "id": s.id,
                    "code": s.code,
                    "matricula": s.matricula,
                    "all_tests_passed": s.all_tests_passed,
                    "compile_error": s.compile_error or "",
                    "tests_passed": sum(1 for tr in s.test_results if tr.passed),
                    "tests_total": len(s.test_results),
                    "diagnosis": {
                        "error_category": s.error_category,
                        "pedagogical_diagnosis": s.pedagogical_diagnosis,
                        "actionable_feedback": s.actionable_feedback,
                    },
                    "submitted_at": s.submitted_at.isoformat(),
                }
                for s in sorted(subs, key=lambda x: _natural_key(x.matricula or "~"))
            ],
        })
    return {
        "exam_id": exam.id,
        "filename": exam.filename,
        "questions": questions,
    }


def get_exam_students(exam: Exam) -> dict:
    # última submissão por (matrícula, questão)
    student_map: dict[str, dict[str, object]] = {}
    for q in exam.questions:
        for s in q.submissions:
            name = s.matricula
            if not name:
                continue
            if name not in student_map:
                student_map[name] = {}
            prev = student_map[name].get(q.number)
            if prev is None or s.id > prev.id:
                student_map[name][q.number] = s

    ordered_qs = sorted_questions(exam)
    question_numbers = [q.number for q in ordered_qs]
    students = []
    for name in sorted(student_map.keys(), key=_natural_key):
        q_subs = student_map[name]
        questions_status = []
        for q in ordered_qs:
            s = q_subs.get(q.number)
            questions_status.append({
                "question_number": q.number,
                "submission_id": s.id if s else None,
                "passed": s.all_tests_passed if s else None,
                "error_category": (s.error_category or "") if s else None,
                "compile_error": bool(s.compile_error) if s else None,
            })
        answered = sum(1 for qs in questions_status if qs["submission_id"] is not None)
        passed = sum(1 for qs in questions_status if qs["passed"])
        students.append({
            "matricula": name,
            "questions": questions_status,
            "answered_count": answered,
            "passed_count": passed,
            "total_questions": len(question_numbers),
        })

    return {"question_numbers": question_numbers, "students": students}


def get_student_detail(exam: Exam, matricula: str, db: Session = None) -> dict:
    best: dict[str, tuple] = {}
    for q in exam.questions:
        for s in q.submissions:
            name = s.matricula
            if name != matricula:
                continue
            prev = best.get(q.number)
            if prev is None or s.id > prev[1].id:
                best[q.number] = (q, s)

    # Mapa (question_id, cluster_label) -> QuestionCluster, p/ ligar a submissão
    # do aluno ao grupo de dificuldade da questão (só existe se o agrupamento rodou).
    cluster_map = {}
    if db is not None:
        q_ids = [q.id for q in exam.questions]
        if q_ids:
            for qc in db.query(QuestionCluster).filter(
                    QuestionCluster.question_id.in_(q_ids)).all():
                cluster_map[(qc.question_id, qc.cluster_label)] = qc

    submissions = []
    for q in sorted_questions(exam):
        if q.number in best:
            _, s = best[q.number]
            qc = cluster_map.get((q.id, s.cluster_id)) if s.cluster_id is not None else None
            submissions.append({
                "question_number": q.number,
                "statement": q.statement,
                "submission_id": s.id,
                "code": s.code,
                "all_tests_passed": s.all_tests_passed,
                "compile_error": s.compile_error or "",
                "error_category": s.error_category or "",
                "pedagogical_diagnosis": s.pedagogical_diagnosis or "",
                "actionable_feedback": s.actionable_feedback or "",
                "submitted_at": s.submitted_at.isoformat(),
                "test_results": [
                    {"input": tr.input, "expected_output": tr.expected_output,
                     "actual_output": tr.actual_output, "passed": tr.passed}
                    for tr in s.test_results
                ],
                "cluster_id": qc.cluster_label if qc else None,
                "cluster_dominant_error": qc.dominant_error if qc else None,
                "cluster_size": qc.size if qc else None,
            })
        else:
            submissions.append({
                "question_number": q.number,
                "statement": q.statement,
                "submission_id": None,
                "code": None,
                "all_tests_passed": None,
                "compile_error": "",
                "error_category": "",
                "pedagogical_diagnosis": "",
                "actionable_feedback": "",
                "submitted_at": None,
                "test_results": [],
                "cluster_id": None,
                "cluster_dominant_error": None,
                "cluster_size": None,
            })

    answered = sum(1 for s in submissions if s["submission_id"] is not None)
    passed = sum(1 for s in submissions if s["all_tests_passed"])
    return {
        "matricula": matricula,
        "total_questions": len(exam.questions),
        "answered_count": answered,
        "passed_count": passed,
        "submissions": submissions,
    }
