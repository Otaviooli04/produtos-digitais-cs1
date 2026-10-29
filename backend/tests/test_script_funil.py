"""Relatório do funil para a equipe: só números, nenhum nome de aluno."""
from datetime import datetime, timedelta

from app.models.orm import Enrollment, Exam, Question, Student, Turma
from scripts.funil import relatorio

AGORA = datetime(2026, 10, 28, 12, 0)


def test_base_vazia_roda_sem_erro(db):
    texto = relatorio(db, agora=AGORA)
    assert "Nenhuma turma cadastrada." in texto
    assert "Matriculados: 0" in texto
    assert "Total desde o início: 0" in texto


def test_turma_aparece_sem_nome_de_aluno(db, professor):
    turma = Turma(nome="CS1 Noite", codigo="CS1", professor_id=professor.id, alunos_previstos=40)
    db.add(turma)
    db.flush()
    exam = Exam(filename="lista.pdf", raw_text="", turma_id=turma.id, publicada=True)
    db.add(exam)
    db.flush()
    db.add(Question(exam_id=exam.id, number="1", statement="Enunciado"))
    aluna = Student(email="beatriz@teste.com", nome="Beatriz Souza", senha_hash="x")
    db.add(aluna)
    db.flush()
    db.add(Enrollment(student_id=aluna.id, turma_id=turma.id, created_at=AGORA - timedelta(days=20)))
    db.commit()

    texto = relatorio(db, agora=AGORA)

    assert "CS1 Noite (Professor Teste)" in texto
    assert "1 matriculados de 40 previstos" in texto
    assert "1 em vermelho" in texto
    assert "Beatriz" not in texto
