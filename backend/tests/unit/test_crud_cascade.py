"""CRUD + exclusão em cascata de turma/prova/questão (sem Docker)."""
import pytest

from app.models.orm import (
    Exam, Question, QuestionCluster, ProcessingJob,
    Submission, SubmissionTestResult, TestCase, Turma,
)
from app.services.exam_service import (
    create_question, delete_exam, delete_question, update_question,
)
from app.services.turma_service import delete_turma, update_turma


@pytest.fixture()
def graph(db, exam_factory, submission_factory):
    """Monta prova→questão→{testcase, submissão→testresult, cluster} + job."""
    exam = exam_factory(questions=[{"number": "1"}])
    q = exam.questions[0]
    db.add(TestCase(question_id=q.id, input="1", expected_output="2"))
    sub = submission_factory(q.id)
    db.add(SubmissionTestResult(
        submission_id=sub.id, input="1", expected_output="2", actual_output="2", passed=True))
    db.add(QuestionCluster(
        question_id=q.id, cluster_label=0, size=1, dominant_error="X",
        representative_submission_id=sub.id))
    db.add(ProcessingJob(kind="bulk_submit", exam_id=exam.id, status="done"))
    db.commit()
    return exam, q, sub


def test_delete_exam_cascade(db, graph):
    exam, q, sub = graph
    eid, qid, sid = exam.id, q.id, sub.id
    delete_exam(exam, db)
    assert db.query(Exam).filter_by(id=eid).first() is None
    assert db.query(Question).filter_by(id=qid).first() is None
    assert db.query(Submission).filter_by(id=sid).first() is None
    assert db.query(SubmissionTestResult).filter_by(submission_id=sid).count() == 0
    assert db.query(QuestionCluster).filter_by(question_id=qid).count() == 0
    assert db.query(TestCase).filter_by(question_id=qid).count() == 0
    assert db.query(ProcessingJob).filter_by(exam_id=eid).count() == 0


def test_delete_question_cascade_keeps_exam(db, graph):
    exam, q, sub = graph
    eid, qid, sid = exam.id, q.id, sub.id
    delete_question(q, db)
    assert db.query(Exam).filter_by(id=eid).first() is not None
    assert db.query(Question).filter_by(id=qid).first() is None
    assert db.query(Submission).filter_by(id=sid).first() is None
    assert db.query(SubmissionTestResult).filter_by(submission_id=sid).count() == 0
    assert db.query(QuestionCluster).filter_by(question_id=qid).count() == 0
    assert db.query(TestCase).filter_by(question_id=qid).count() == 0


def test_delete_turma_cascade(db, graph):
    exam, q, sub = graph
    turma = db.query(Turma).filter_by(id=exam.turma_id).first()
    tid, eid, sid = turma.id, exam.id, sub.id
    delete_turma(turma, db)
    assert db.query(Turma).filter_by(id=tid).first() is None
    assert db.query(Exam).filter_by(id=eid).first() is None
    assert db.query(Submission).filter_by(id=sid).first() is None


def test_create_and_update_question(db, exam_factory):
    exam = exam_factory(questions=[])
    q = create_question(exam.id, {
        "number": "5",
        "statement": "Some um vetor.",
        "required_structures": ["For"],
        "forbidden_structures": [],
        "requires_loop": True,
        "required_functions": [{"name": "soma", "param_count": 2, "return_type": "int",
                                "requires_recursion": False, "requires_pointer_param": False}],
    }, db)
    assert q.id is not None
    assert q.requires_loop is True

    # update parcial: só o enunciado e estruturas; demais preservados
    update_question(q, {"statement": "Novo enunciado.", "required_structures": ["While"]}, db)
    refreshed = db.query(Question).filter_by(id=q.id).first()
    assert refreshed.statement == "Novo enunciado."
    assert refreshed.required_structures == ["While"]
    assert refreshed.requires_loop is True  # não foi tocado
    assert refreshed.required_functions[0]["name"] == "soma"
