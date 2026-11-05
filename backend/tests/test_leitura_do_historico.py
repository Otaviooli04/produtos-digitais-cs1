"""Leitura do histórico do aluno: listas e trilha numa lista só, em ordem."""
from datetime import datetime, timedelta

import pytest

from app.models.orm import ExercicioGerado, Student, Submission, TentativaDeTreino
from app.services.historico_do_aluno import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, ler_historico,
)

T0 = datetime(2026, 10, 28, 12, 0)
OFF = "Acesso Fora dos Limites: Off-by-One"


@pytest.fixture()
def aluno(db):
    s = Student(email="historico@aluno.com", nome="Aluno Histórico", senha_hash="x")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@pytest.fixture()
def questao(exam_factory):
    return exam_factory(questions=[{"number": "1"}]).questions[0]


def _envio(db, aluno, questao, minutos, categoria):
    sub = Submission(
        question_id=questao.id, code="int main(){}", error_category=categoria,
        all_tests_passed=categoria == "Correto", actionable_feedback="faça assim",
        student_id=aluno.id, submitted_at=T0 + timedelta(minutes=minutos),
    )
    db.add(sub)
    return sub


def _exercicio(db, aluno, reportado=False):
    e = ExercicioGerado(student_id=aluno.id, error_category=OFF, titulo="Soma dos pares",
                        enunciado="Some os pares.", casos_teste=[], reportado=reportado)
    db.add(e)
    db.flush()
    return e


def _tentativa(db, aluno, exercicio, minutos, passou, categoria):
    db.add(TentativaDeTreino(
        exercicio_id=exercicio.id, student_id=aluno.id, code="int main(){}",
        all_tests_passed=passou, error_category=categoria,
        submitted_at=T0 + timedelta(minutes=minutos),
    ))


def test_junta_listas_e_trilha_em_ordem_de_tempo(db, aluno, questao):
    exercicio = _exercicio(db, aluno)
    _envio(db, aluno, questao, 20, "Correto")
    _tentativa(db, aluno, exercicio, 10, True, "Correto")
    _envio(db, aluno, questao, 0, OFF)
    db.commit()

    envios = ler_historico(aluno, db)
    assert [(e.origem, e.resultado) for e in envios] == [
        (LISTA, ERRO), (TRILHA, ACERTO), (LISTA, ACERTO)]
    assert envios[0].item_id == questao.id
    assert envios[0].o_que_fazer == "faça assim"
    assert envios[1].item_id == exercicio.id
    assert envios[1].alvo == OFF
    assert envios[1].titulo == "Soma dos pares"


def test_no_empate_a_lista_vem_antes_da_trilha(db, aluno, questao):
    exercicio = _exercicio(db, aluno)
    _tentativa(db, aluno, exercicio, 0, False, OFF)
    _envio(db, aluno, questao, 0, OFF)
    db.commit()

    assert [e.origem for e in ler_historico(aluno, db)] == [LISTA, TRILHA]


def test_tentativa_de_exercicio_reportado_fica_de_fora(db, aluno):
    exercicio = _exercicio(db, aluno, reportado=True)
    _tentativa(db, aluno, exercicio, 0, True, "Correto")
    db.commit()

    assert ler_historico(aluno, db) == []


def test_envio_sem_momento_fica_de_fora_e_falha_e_classificada(db, aluno, questao):
    _envio(db, aluno, questao, 0, "Erro Desconhecido")
    sem_momento = _envio(db, aluno, questao, 1, OFF)
    db.commit()
    sem_momento.submitted_at = None
    db.commit()

    (envio,) = ler_historico(aluno, db)
    assert envio.resultado == FALHA


def test_envio_de_outro_aluno_nao_entra(db, aluno, questao):
    outro = Student(email="outro@aluno.com", nome="Outro", senha_hash="x")
    db.add(outro)
    db.flush()
    exercicio = _exercicio(db, outro)
    _envio(db, outro, questao, 0, OFF)
    _tentativa(db, outro, exercicio, 1, False, OFF)
    db.commit()

    assert ler_historico(aluno, db) == []
