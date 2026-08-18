from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_professor
from app.auth.ownership import get_exam_or_404, get_question_or_404
from app.engine.error_locator import parse_compile_error_lines
from app.llm.feedback_generator import generate_cluster_insights
from app.ml.cluster import FeatureStrategy, cluster_question
from app.models.database import get_db
from app.models.orm import Exam, Professor, Question, QuestionCluster, TestCase as TestCaseORM
from app.models.schemas import (
    ClusterInfo,
    ClusteringResponse,
    ClusterInsight,
    ExamResponse,
    ExamResultsResponse,
    ExamStudentsResponse,
    ExamUpdate,
    ExamUploadStartResponse,
    InsightsResponse,
    JobStartResponse,
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
    ScatterPoint,
    StudentDetailResponse,
    TestCaseAddRequest,
    TestCaseResponse,
    TestCaseUpdateRequest,
)
from app.services.bulk_submission_service import start_bulk_processing
from app.services.exam_service import (
    add_test_cases,
    create_question,
    delete_exam,
    delete_question,
    get_exam_results,
    get_exam_students,
    get_student_detail,
    start_exam_processing,
    update_exam,
    update_question,
)

router = APIRouter(prefix="/exam", tags=["exam"])


def _failing_summary(submissions) -> dict:
    """Por grupo (cluster_id): rótulo do sintoma e QUANTOS casos de teste o grupo
    falha. Só rotula quando todos os membros compartilham a MESMA assinatura de
    falha (grupo coeso); grupos de assinatura mista ficam sem rótulo/contagem.
    O grupo "Correto" recebe contagem 0. Usado para descrever e ORDENAR os
    cartões (mais casos falhos = dificuldade mais severa)."""
    from app.ml.cluster import failure_signature
    sigs_by_label: dict = {}
    for s in submissions:
        if s.cluster_id is not None:
            sigs_by_label.setdefault(s.cluster_id, set()).add(failure_signature(s))

    out: dict = {}
    for label, sigs in sigs_by_label.items():
        if len(sigs) != 1:
            out[label] = (None, None)
            continue
        sig = next(iter(sigs))
        if not sig:
            out[label] = (None, None)
            continue
        failed = [i + 1 for i, ok in enumerate(sig) if not ok]
        if not failed:
            out[label] = (None, 0)
        elif len(failed) == len(sig):
            out[label] = ("falha todos os casos", len(failed))
        elif len(failed) == 1:
            out[label] = (f"falha o caso {failed[0]}", 1)
        else:
            out[label] = ("falha os casos " + ", ".join(map(str, failed)), len(failed))
    return out


def _highlight_for(qc, llm_lines) -> list:
    """Linhas a destacar no código representativo do grupo. Erro de COMPILAÇÃO usa o
    parse determinístico do gcc (autoritativo, linha exata); senão, usa a atribuição
    do Gemini (erro de lógica). Sem representativo → nada a destacar."""
    rep = qc.representative
    if rep is None:
        return []
    if rep.compile_error:
        return parse_compile_error_lines(
            rep.compile_error, max_line=len((rep.code or "").split("\n")))
    return llm_lines or []


# ── público: alunos precisam carregar a prova antes de submeter ──────────────
@router.get("/{exam_id}", response_model=ExamResponse)
def get_exam(exam_id: int, db: Session = Depends(get_db)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Prova não encontrada.")
    return _exam_to_response(exam)


# ── rotas protegidas (professor autenticado) ─────────────────────────────────
@router.post("/upload", response_model=ExamUploadStartResponse)
async def upload_exam(
    file: UploadFile = File(...),
    turma_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    if not file.filename.endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(status_code=400, detail="Formato inválido. Envie PDF ou DOCX.")
    # Verifica que a turma pertence ao professor
    if turma_id is not None:
        from app.models.orm import Turma
        turma = db.query(Turma).filter(
            Turma.id == turma_id,
            Turma.professor_id == professor.id,
        ).first()
        if not turma:
            raise HTTPException(status_code=404, detail="Turma não encontrada.")
    file_bytes = await file.read()
    try:
        exam, job = start_exam_processing(
            file_bytes, file.filename, db, turma_id=turma_id, professor_id=professor.id)
        return ExamUploadStartResponse(exam_id=exam.id, job_id=job.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{exam_id}", response_model=ExamResponse)
def patch_exam(
    exam_id: int,
    body: ExamUpdate,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    exam = get_exam_or_404(exam_id, db, professor_id=professor.id)
    if body.turma_id is not None:
        from app.models.orm import Turma
        turma = db.query(Turma).filter(
            Turma.id == body.turma_id, Turma.professor_id == professor.id,
        ).first()
        if not turma:
            raise HTTPException(status_code=404, detail="Turma não encontrada.")
    update_exam(
        exam, db,
        filename=body.filename,
        turma_id=body.turma_id,
        modo=body.modo,
        abre_em=body.abre_em,
        fecha_em=body.fecha_em,
        max_tentativas=body.max_tentativas,
        limpar=body.limpar,
    )
    return _exam_to_response(exam)


@router.delete("/{exam_id}", status_code=204)
def remove_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    exam = get_exam_or_404(exam_id, db, professor_id=professor.id)
    delete_exam(exam, db)


@router.post("/{exam_id}/questions", response_model=QuestionResponse, status_code=201)
def post_question(
    exam_id: int,
    body: QuestionCreate,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    exam = get_exam_or_404(exam_id, db, professor_id=professor.id)
    if any(q.number == body.number for q in exam.questions):
        raise HTTPException(status_code=409, detail=f"Já existe a questão {body.number}.")
    question = create_question(exam.id, body.model_dump(), db)
    return _question_to_response(question)


@router.put("/{exam_id}/questions/{question_number}", response_model=QuestionResponse)
def put_question(
    exam_id: int,
    question_number: str,
    body: QuestionUpdate,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    update_question(question, body.model_dump(exclude_unset=True), db)
    return _question_to_response(question)


@router.delete("/{exam_id}/questions/{question_number}", status_code=204)
def remove_question(
    exam_id: int,
    question_number: str,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    delete_question(question, db)


@router.get("/{exam_id}/questions/{question_number}/testcases", response_model=list[TestCaseResponse])
def list_question_testcases(
    exam_id: int,
    question_number: str,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    return [TestCaseResponse(id=tc.id, input=tc.input, expected_output=tc.expected_output) for tc in question.test_cases]


@router.post("/{exam_id}/questions/{question_number}/testcases")
def add_question_testcases(
    exam_id: int,
    question_number: str,
    body: TestCaseAddRequest,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    count = add_test_cases(question.id, [tc.model_dump() for tc in body.test_cases], db)
    return {"added": count, "question_number": question_number}


@router.put("/{exam_id}/questions/{question_number}/testcases/{tc_id}", response_model=TestCaseResponse)
def update_question_testcase(
    exam_id: int,
    question_number: str,
    tc_id: int,
    body: TestCaseUpdateRequest,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    tc = db.query(TestCaseORM).filter(
        TestCaseORM.id == tc_id,
        TestCaseORM.question_id == question.id,
    ).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Test case não encontrado.")
    tc.input = body.input
    tc.expected_output = body.expected_output
    db.commit()
    db.refresh(tc)
    return TestCaseResponse(id=tc.id, input=tc.input, expected_output=tc.expected_output)


@router.delete("/{exam_id}/questions/{question_number}/testcases/{tc_id}", status_code=204)
def delete_question_testcase(
    exam_id: int,
    question_number: str,
    tc_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    tc = db.query(TestCaseORM).filter(
        TestCaseORM.id == tc_id,
        TestCaseORM.question_id == question.id,
    ).first()
    if not tc:
        raise HTTPException(status_code=404, detail="Test case não encontrado.")
    db.delete(tc)
    db.commit()


@router.post("/{exam_id}/submissions/bulk", response_model=JobStartResponse)
async def bulk_submit(
    exam_id: int,
    file: UploadFile = File(...),
    format: str = Form(...),
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Envie um arquivo .zip.")
    if format not in ("by_student", "by_question"):
        raise HTTPException(status_code=400, detail="format deve ser 'by_student' ou 'by_question'.")
    get_exam_or_404(exam_id, db, professor_id=professor.id)
    zip_bytes = await file.read()
    try:
        job = start_bulk_processing(zip_bytes, exam_id, format, db, professor_id=professor.id)
        return JobStartResponse(job_id=job.id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar ZIP: {e}")


@router.get("/{exam_id}/students", response_model=ExamStudentsResponse)
def get_students(
    exam_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    exam = get_exam_or_404(exam_id, db, professor_id=professor.id)
    return get_exam_students(exam)


@router.get("/{exam_id}/students/detail", response_model=StudentDetailResponse)
def get_student(
    exam_id: int,
    matricula: str = Query(...),
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    exam = get_exam_or_404(exam_id, db, professor_id=professor.id)
    return get_student_detail(exam, matricula, db)


@router.get("/{exam_id}/results", response_model=ExamResultsResponse)
def get_results(
    exam_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    exam = get_exam_or_404(exam_id, db, professor_id=professor.id)
    return get_exam_results(exam)


@router.post("/{exam_id}/questions/{question_number}/cluster", response_model=ClusteringResponse)
def run_clustering(
    exam_id: int,
    question_number: str,
    strategy: FeatureStrategy = Query(default=FeatureStrategy.TFIDF),
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    result = cluster_question(question.id, db, strategy=strategy)
    if result is None:
        raise HTTPException(status_code=422, detail="Submissões insuficientes para clustering (mínimo 3).")

    db.refresh(question)
    clusters_db = db.query(QuestionCluster).filter(QuestionCluster.question_id == question.id).all()
    clusters_map = {qc.cluster_label: qc for qc in clusters_db}
    failing = _failing_summary(question.submissions)
    clusters_out = [
        ClusterInfo(
            cluster_id=c["cluster_id"],
            size=c["size"],
            dominant_error=c["dominant_error"],
            failing_label=failing.get(c["cluster_id"], (None, None))[0],
            failing_count=failing.get(c["cluster_id"], (None, None))[1],
            representative_submission_id=clusters_map[c["cluster_id"]].representative_submission_id
            if c["cluster_id"] in clusters_map else None,
            representative_matricula=clusters_map[c["cluster_id"]].representative.matricula
            if c["cluster_id"] in clusters_map and clusters_map[c["cluster_id"]].representative else None,
            representative_code=clusters_map[c["cluster_id"]].representative.code
            if c["cluster_id"] in clusters_map and clusters_map[c["cluster_id"]].representative else None,
        )
        for c in result.clusters
    ]
    return ClusteringResponse(
        question_number=question_number,
        total_submissions=len(result.scatter),
        clusters=clusters_out,
        scatter=[ScatterPoint(**p) for p in result.scatter],
        strategy=result.strategy.value,
        silhouette_score=result.silhouette,
    )


@router.get("/{exam_id}/questions/{question_number}/groups")
def get_groups(
    exam_id: int,
    question_number: str,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    """Grupos de dificuldade já salvos, sem re-rodar. Alimenta a aba ao abrir:
    o agrupamento roda automaticamente no fim do lote (ou via 'Recalcular')."""
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    clusters_db = db.query(QuestionCluster).filter(
        QuestionCluster.question_id == question.id).all()
    if not clusters_db:
        return {"has_groups": False, "question_number": question_number}

    scatter = [
        {"x": float(s.umap_x), "y": float(s.umap_y),
         "cluster_id": s.cluster_id, "matricula": s.matricula}
        for s in question.submissions
        if s.cluster_id is not None and s.umap_x is not None and s.umap_y is not None
    ]
    # Rótulo do sintoma por grupo: quais (e quantos) casos de teste o grupo falha.
    failing = _failing_summary(question.submissions)
    clusters = [
        {"cluster_id": qc.cluster_label, "size": qc.size,
         "dominant_error": qc.dominant_error,
         "failing_label": failing.get(qc.cluster_label, (None, None))[0],
         "failing_count": failing.get(qc.cluster_label, (None, None))[1],
         "representative_submission_id": qc.representative_submission_id,
         "representative_matricula": qc.representative.matricula if qc.representative else None,
         "representative_code": qc.representative.code if qc.representative else None}
        for qc in clusters_db
    ]
    insights = [
        {"cluster_id": qc.cluster_label, "size": qc.size,
         "dominant_error": qc.dominant_error, "insight": qc.insight or "",
         "highlight_lines": _highlight_for(qc, qc.highlight_lines)}
        for qc in clusters_db
    ]
    return {
        "has_groups": True,
        "question_number": question_number,
        "total_submissions": len(scatter),
        "clusters": clusters,
        "scatter": scatter,
        "silhouette_score": None,
        "strategy": "tfidf_behavioral",
        "insights": insights,
    }


@router.post("/{exam_id}/questions/{question_number}/insights", response_model=InsightsResponse)
def run_insights(
    exam_id: int,
    question_number: str,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    clusters_db = db.query(QuestionCluster).filter(QuestionCluster.question_id == question.id).all()
    if not clusters_db:
        raise HTTPException(status_code=422, detail="Nenhum cluster encontrado. Execute o clustering antes de gerar insights.")

    # Só gera via Gemini os clusters ainda sem insight salvo (ou todos se force).
    # O insight fica persistido em QuestionCluster; re-clusterizar apaga as linhas
    # e invalida o cache naturalmente.
    pending = [qc for qc in clusters_db if force or not qc.insight]
    if pending:
        payload = [
            {
                "cluster_id": qc.cluster_label,
                "size": qc.size,
                "dominant_error": qc.dominant_error,
                "representative_code": qc.representative.code if qc.representative else "",
            }
            for qc in pending
        ]
        try:
            generated = generate_cluster_insights(question.statement, payload)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))
        by_label = {qc.cluster_label: qc for qc in pending}
        for item in generated:
            qc = by_label.get(item["cluster_id"])
            if qc is not None:
                qc.insight = item["insight"]
                qc.highlight_lines = _highlight_for(qc, item.get("highlight_lines"))
        db.commit()

    return InsightsResponse(
        question_number=question_number,
        insights=[
            ClusterInsight(
                cluster_id=qc.cluster_label,
                size=qc.size,
                dominant_error=qc.dominant_error,
                insight=qc.insight or "",
                highlight_lines=_highlight_for(qc, qc.highlight_lines),
            )
            for qc in clusters_db
        ],
    )


@router.get("/{exam_id}/questions/{question_number}/submissions")
def get_question_submissions(
    exam_id: int,
    question_number: str,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    question = get_question_or_404(exam_id, question_number, db, professor_id=professor.id)
    return {
        "question_number": question_number,
        "statement": question.statement,
        "submissions": [
            {
                "id": s.id,
                "matricula": s.matricula,
                "code": s.code,
                "compile_error": s.compile_error or "",
                "warnings": s.warnings or "",
                "all_tests_passed": s.all_tests_passed,
                "error_category": s.error_category or "",
                "pedagogical_diagnosis": s.pedagogical_diagnosis or "",
                "actionable_feedback": s.actionable_feedback or "",
                "test_results": [
                    {"input": tr.input, "expected_output": tr.expected_output,
                     "actual_output": tr.actual_output, "passed": tr.passed}
                    for tr in s.test_results
                ],
                "submitted_at": s.submitted_at.isoformat(),
            }
            for s in question.submissions
        ],
    }


_SINGLE_LINE_HINTS = (
    "uma unica linha", "uma única linha", "em uma linha", "numa unica linha",
    "numa única linha", "em uma so linha", "em uma só linha",
    "um unico caractere", "um único caractere",
)


def _question_warnings(q: Question) -> list[str]:
    """Sinaliza extrações suspeitas para o professor revisar antes de confiar no veredito."""
    warnings = []

    subs = q.submissions
    if subs and not any(s.all_tests_passed for s in subs):
        warnings.append(
            f"Nenhuma das {len(subs)} submissões passou. Pode ser que o gabarito ou "
            "as estruturas exigidas estejam errados. Confira os casos de teste."
        )

    statement = (q.statement or "").lower()
    if any(h in statement for h in _SINGLE_LINE_HINTS) and any(
        "\n" in (tc.expected_output or "") for tc in q.test_cases
    ):
        warnings.append(
            "Algum caso de teste tem a saída esperada quebrada em mais de uma linha, "
            "mas o enunciado pede uma única linha. Pode ser quebra de linha do PDF."
        )

    return warnings


def _question_to_response(q: Question) -> QuestionResponse:
    return QuestionResponse(
        id=q.id,
        number=q.number,
        statement=q.statement,
        points=q.points if q.points is not None else 1.0,
        required_structures=q.required_structures or [],
        forbidden_structures=q.forbidden_structures or [],
        requires_loop=q.requires_loop,
        required_functions=q.required_functions or [],
        test_case_count=len(q.test_cases),
        warnings=_question_warnings(q),
    )


def _question_sort_key(q):
    """Ordena por número da questão (numérico quando possível: 2 antes de 10)."""
    try:
        return (0, int(q.number))
    except (TypeError, ValueError):
        return (1, q.number or "")


def _exam_to_response(exam: Exam) -> ExamResponse:
    return ExamResponse(
        id=exam.id,
        filename=exam.filename,
        created_at=exam.created_at.isoformat() if exam.created_at else "",
        turma_id=exam.turma_id,
        turma_nome=exam.turma.nome if exam.turma else None,
        total_points=sum((q.points if q.points is not None else 1.0) for q in exam.questions),
        modo=exam.modo or "prova",
        abre_em=exam.abre_em.isoformat() if exam.abre_em else None,
        fecha_em=exam.fecha_em.isoformat() if exam.fecha_em else None,
        max_tentativas=exam.max_tentativas,
        questions=[_question_to_response(q) for q in sorted(exam.questions, key=_question_sort_key)],
    )
