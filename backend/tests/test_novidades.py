"""Novidades do aluno: o que chegou para ele e ele ainda não abriu.

A resposta do professor vira novidade para quem tem a tentativa mais recente no
grupo, e o exercício pré-gerado da trilha também. A tela que entrega a resposta
ou o exercício marca como vista, e a leitura só mostra a que ainda vale."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.orm import (
    Enrollment, ExercicioGerado, Novidade, QuestionCluster, Student, Submission,
)

AGORA = datetime(2026, 11, 4, 12, 0)
CHAVE = "cat:Saída Incorreta"
OUTRA_CHAVE = "cat:Tudo no Main"


@pytest.fixture()
def prova(exam_factory):
    return exam_factory(questions=[{"number": "1"}, {"number": "2"}], titulo="Lista 3")


def _matricular(db, nome, email, turma_id):
    s = Student(email=email, nome=nome, senha_hash="x")
    db.add(s)
    db.flush()
    db.add(Enrollment(student_id=s.id, turma_id=turma_id))
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture()
def aluno(db, prova):
    return _matricular(db, "Ana", "ana@teste.com", prova.turma_id)


@pytest.fixture()
def colega(db, prova):
    return _matricular(db, "Bia", "bia@teste.com", prova.turma_id)


def _questao(prova, numero="1"):
    return next(q for q in prova.questions if q.number == numero)


def _envio(db, questao, student_id, tentativa, cluster_id, categoria="Saída Incorreta"):
    sub = Submission(
        question_id=questao.id, code="int main(){}", error_category=categoria,
        all_tests_passed=False, student_id=student_id, attempt_number=tentativa,
        cluster_id=cluster_id, submitted_at=AGORA - timedelta(hours=1),
    )
    db.add(sub)
    db.commit()
    return sub


def _grupo(db, questao, label=0, chave=CHAVE, resposta="Revejam a condição de parada.",
           em=AGORA):
    grupo = QuestionCluster(
        question_id=questao.id, cluster_label=label, chave=chave, size=1,
        dominant_error="Saída Incorreta", resposta_professor=resposta, resposta_em=em,
    )
    db.add(grupo)
    db.commit()
    db.refresh(grupo)
    return grupo


def _exercicio(db, student_id, resolvido=False, reportado=False, titulo="Soma dos pares"):
    exercicio = ExercicioGerado(
        student_id=student_id, error_category="Tudo no Main", titulo=titulo,
        enunciado="Some os pares.", casos_teste=[], resolvido=resolvido,
        reportado=reportado, created_at=AGORA,
    )
    db.add(exercicio)
    db.commit()
    db.refresh(exercicio)
    return exercicio


def _novidade(db, student_id, questao=None, chave=CHAVE, exercicio=None, chegou_em=AGORA,
              vista_em=None):
    novidade = Novidade(
        student_id=student_id,
        tipo="exercicio" if exercicio else "retorno",
        question_id=None if exercicio else questao.id,
        grupo_chave=None if exercicio else chave,
        exercicio_id=exercicio.id if exercicio else None,
        chegou_em=chegou_em,
        vista_em=vista_em,
    )
    db.add(novidade)
    db.commit()
    db.refresh(novidade)
    return novidade


class TestTabela:
    def test_duas_nao_vistas_do_mesmo_grupo_sao_recusadas(self, db, aluno, prova):
        _novidade(db, aluno.id, _questao(prova))
        db.add(Novidade(student_id=aluno.id, tipo="retorno", question_id=_questao(prova).id,
                        grupo_chave=CHAVE, chegou_em=AGORA))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()

    def test_depois_de_vista_aceita_outra_do_mesmo_grupo(self, db, aluno, prova):
        _novidade(db, aluno.id, _questao(prova), vista_em=AGORA)
        _novidade(db, aluno.id, _questao(prova), chegou_em=AGORA + timedelta(hours=1))
        assert db.query(Novidade).count() == 2

    def test_exercicio_nao_visto_e_um_so_por_exercicio(self, db, aluno):
        exercicio = _exercicio(db, aluno.id)
        _novidade(db, aluno.id, exercicio=exercicio)
        db.add(Novidade(student_id=aluno.id, tipo="exercicio", exercicio_id=exercicio.id,
                        chegou_em=AGORA))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
