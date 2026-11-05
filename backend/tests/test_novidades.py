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
from app.services.novidades_service import (
    marcar_exercicio_visto, marcar_resposta_vista, registrar_exercicio, registrar_resposta,
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


class TestNascimento:
    def test_resposta_cria_para_quem_tem_a_tentativa_mais_recente_no_grupo(
        self, db, aluno, colega, prova
    ):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _envio(db, q, colega.id, 1, cluster_id=0)
        registrar_resposta(_grupo(db, q), db)
        novidades = db.query(Novidade).order_by(Novidade.student_id).all()
        assert [n.student_id for n in novidades] == sorted([aluno.id, colega.id])
        assert all(n.tipo == "retorno" for n in novidades)
        assert all(n.question_id == q.id and n.grupo_chave == CHAVE for n in novidades)
        assert all(n.chegou_em == AGORA and n.vista_em is None for n in novidades)

    def test_tentativa_antiga_no_grupo_nao_basta(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _envio(db, q, aluno.id, 2, cluster_id=1, categoria="Tudo no Main")
        registrar_resposta(_grupo(db, q), db)
        assert db.query(Novidade).count() == 0

    def test_envio_sem_conta_nao_cria(self, db, prova):
        q = _questao(prova)
        _envio(db, q, None, 1, cluster_id=0)
        registrar_resposta(_grupo(db, q), db)
        assert db.query(Novidade).count() == 0

    def test_atividade_nao_publicada_nao_cria(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        prova.publicada = False
        db.commit()
        registrar_resposta(_grupo(db, q), db)
        assert db.query(Novidade).count() == 0

    def test_grupo_sem_chave_nao_cria(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        registrar_resposta(_grupo(db, q, chave=None), db)
        assert db.query(Novidade).count() == 0

    def test_editar_antes_de_ver_nao_duplica(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        registrar_resposta(grupo, db)
        grupo.resposta_professor = "Texto corrigido."
        grupo.resposta_em = AGORA + timedelta(hours=1)
        db.commit()
        registrar_resposta(grupo, db)
        (novidade,) = db.query(Novidade).all()
        assert novidade.chegou_em == AGORA

    def test_editar_depois_de_ver_cria_outra(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        registrar_resposta(grupo, db)
        marcar_resposta_vista(aluno.id, q.id, CHAVE, db, agora=AGORA + timedelta(minutes=5))
        grupo.resposta_professor = "Texto corrigido."
        grupo.resposta_em = AGORA + timedelta(hours=1)
        db.commit()
        registrar_resposta(grupo, db)
        novidades = db.query(Novidade).order_by(Novidade.chegou_em).all()
        assert [n.chegou_em for n in novidades] == [AGORA, AGORA + timedelta(hours=1)]
        assert novidades[0].vista_em == AGORA + timedelta(minutes=5)
        assert novidades[1].vista_em is None

    def test_salvar_o_mesmo_texto_depois_de_ver_nao_cria_outra(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        registrar_resposta(grupo, db)
        marcar_resposta_vista(aluno.id, q.id, CHAVE, db, agora=AGORA + timedelta(minutes=5))
        texto = grupo.resposta_professor
        grupo.resposta_em = AGORA + timedelta(hours=1)
        db.commit()
        registrar_resposta(grupo, db, anterior=texto)
        (novidade,) = db.query(Novidade).all()
        assert novidade.chegou_em == AGORA
        assert novidade.vista_em == AGORA + timedelta(minutes=5)

    def test_mudar_o_texto_depois_de_ver_cria_outra_com_anterior(self, db, aluno, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        registrar_resposta(grupo, db)
        marcar_resposta_vista(aluno.id, q.id, CHAVE, db, agora=AGORA + timedelta(minutes=5))
        velho = grupo.resposta_professor
        grupo.resposta_professor = "Texto corrigido."
        grupo.resposta_em = AGORA + timedelta(hours=1)
        db.commit()
        registrar_resposta(grupo, db, anterior=velho)
        novidades = db.query(Novidade).order_by(Novidade.chegou_em).all()
        assert [n.chegou_em for n in novidades] == [AGORA, AGORA + timedelta(hours=1)]
        assert novidades[1].vista_em is None

    def test_apagar_a_resposta_remove_so_as_nao_vistas(self, db, aluno, colega, prova):
        q = _questao(prova)
        _envio(db, q, aluno.id, 1, cluster_id=0)
        _envio(db, q, colega.id, 1, cluster_id=0)
        grupo = _grupo(db, q)
        registrar_resposta(grupo, db)
        marcar_resposta_vista(aluno.id, q.id, CHAVE, db, agora=AGORA)
        grupo.resposta_professor = None
        grupo.resposta_em = None
        db.commit()
        registrar_resposta(grupo, db)
        (ficou,) = db.query(Novidade).all()
        assert ficou.student_id == aluno.id
        assert ficou.vista_em == AGORA

    def test_exercicio_gravado_duas_vezes_fica_um(self, db, aluno):
        exercicio = _exercicio(db, aluno.id)
        registrar_exercicio(exercicio, db)
        registrar_exercicio(exercicio, db)
        (novidade,) = db.query(Novidade).all()
        assert novidade.tipo == "exercicio"
        assert novidade.exercicio_id == exercicio.id
        assert novidade.chegou_em == AGORA


class TestMarcarComoVista:
    def test_marcar_a_resposta_so_mexe_no_grupo_dela(self, db, aluno, prova):
        q = _questao(prova)
        _novidade(db, aluno.id, q, chave=CHAVE)
        _novidade(db, aluno.id, q, chave=OUTRA_CHAVE)
        marcar_resposta_vista(aluno.id, q.id, CHAVE, db, agora=AGORA)
        vistas = {n.grupo_chave: n.vista_em for n in db.query(Novidade).all()}
        assert vistas == {CHAVE: AGORA, OUTRA_CHAVE: None}

    def test_marcar_o_exercicio_preenche_vista_em(self, db, aluno):
        exercicio = _exercicio(db, aluno.id)
        _novidade(db, aluno.id, exercicio=exercicio)
        marcar_exercicio_visto(aluno.id, exercicio.id, db, agora=AGORA)
        assert db.query(Novidade).one().vista_em == AGORA
