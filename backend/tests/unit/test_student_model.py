"""Conta do aluno: turma com código de acesso, vínculo aluno↔turma e tentativas."""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.orm import Enrollment, Student, Submission, Turma
from app.services.turma_service import _ALFABETO_CODIGO, create_turma, delete_turma


@pytest.fixture()
def student(db):
    aluno = Student(
        email="aluno@teste.com", nome="Aluno Teste", matricula="2026001", senha_hash="x")
    db.add(aluno)
    db.commit()
    db.refresh(aluno)
    return aluno


def test_create_turma_gera_codigo_acesso(db, professor):
    turma = create_turma("Algoritmos", "COMP101", db, professor_id=professor.id)
    assert turma.codigo_acesso is not None
    assert len(turma.codigo_acesso) == 6
    assert set(turma.codigo_acesso) <= set(_ALFABETO_CODIGO)
    # sem caracteres ambíguos, porque o código é ditado em sala
    assert not set(turma.codigo_acesso) & set("O0I1")


def test_codigo_acesso_e_unico_entre_turmas(db, professor):
    codigos = {
        create_turma(f"Turma {i}", f"C{i}", db, professor_id=professor.id).codigo_acesso
        for i in range(5)
    }
    assert len(codigos) == 5


def test_aluno_nao_entra_duas_vezes_na_mesma_turma(db, professor, student):
    turma = create_turma("Algoritmos", "COMP101", db, professor_id=professor.id)
    db.add(Enrollment(student_id=student.id, turma_id=turma.id))
    db.commit()

    db.add(Enrollment(student_id=student.id, turma_id=turma.id))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()
    assert db.query(Enrollment).filter_by(student_id=student.id).count() == 1


def test_delete_turma_remove_vinculos(db, professor, student):
    turma = create_turma("Algoritmos", "COMP101", db, professor_id=professor.id)
    db.add(Enrollment(student_id=student.id, turma_id=turma.id))
    db.commit()
    tid, sid = turma.id, student.id

    delete_turma(turma, db)
    assert db.query(Turma).filter_by(id=tid).first() is None
    assert db.query(Enrollment).filter_by(turma_id=tid).count() == 0
    assert db.query(Student).filter_by(id=sid).first() is not None  # o aluno sobrevive


def test_submissao_liga_aluno_e_numera_tentativa(db, exam_factory, submission_factory, student):
    exam = exam_factory(questions=[{"number": "1"}])
    question = exam.questions[0]

    for tentativa in (1, 2):
        sub = submission_factory(question.id)
        sub.student_id = student.id
        sub.matricula = student.matricula
        sub.attempt_number = tentativa
        db.commit()

    tentativas = (
        db.query(Submission)
        .filter_by(question_id=question.id, student_id=student.id)
        .order_by(Submission.attempt_number)
        .all()
    )
    assert [s.attempt_number for s in tentativas] == [1, 2]
    assert tentativas[0].student.email == "aluno@teste.com"
    assert len(student.submissions) == 2
