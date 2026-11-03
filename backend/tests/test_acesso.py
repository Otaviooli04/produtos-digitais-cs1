"""Registro de acesso do aluno (RF14): descarte em 30 minutos e origem aceita."""
from datetime import datetime, timedelta

import pytest

from app.auth.service import create_access_token
from app.auth.student_service import create_student_token
from app.models.orm import Acesso, Student
from app.services.acesso_service import registrar_acesso

AGORA = datetime(2026, 10, 28, 12, 0)


@pytest.fixture()
def aluno(db):
    s = Student(email="ana@teste.com", nome="Ana", senha_hash="x")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _vias(db, aluno):
    return [a.via for a in
            db.query(Acesso).filter_by(student_id=aluno.id).order_by(Acesso.momento).all()]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestRegistrarAcesso:
    def test_grava_o_primeiro_acesso(self, db, aluno):
        assert registrar_acesso(aluno.id, None, db, agora=AGORA) is True
        acesso = db.query(Acesso).one()
        assert acesso.momento == AGORA
        assert acesso.via is None

    def test_sem_origem_descarta_antes_de_30_minutos_e_grava_com_30(self, db, aluno):
        registrar_acesso(aluno.id, None, db, agora=AGORA)
        assert registrar_acesso(aluno.id, None, db, agora=AGORA + timedelta(minutes=29)) is False
        assert registrar_acesso(aluno.id, None, db, agora=AGORA + timedelta(minutes=30)) is True
        assert _vias(db, aluno) == [None, None]

    def test_sem_origem_logo_depois_do_convite_e_descartado(self, db, aluno):
        registrar_acesso(aluno.id, "convite", db, agora=AGORA)
        assert registrar_acesso(aluno.id, None, db, agora=AGORA + timedelta(minutes=5)) is False
        assert _vias(db, aluno) == ["convite"]

    def test_convite_logo_depois_de_abrir_grava_e_o_segundo_nao(self, db, aluno):
        registrar_acesso(aluno.id, None, db, agora=AGORA)
        assert registrar_acesso(aluno.id, "convite", db, agora=AGORA + timedelta(minutes=5)) is True
        assert registrar_acesso(aluno.id, "convite", db, agora=AGORA + timedelta(minutes=6)) is False
        assert _vias(db, aluno) == [None, "convite"]

    @pytest.mark.parametrize("recebida, gravada", [
        (" Convite ", "convite"),
        ("", None),
        ("whatsapp", None),
    ])
    def test_origem_normalizada(self, db, aluno, recebida, gravada):
        registrar_acesso(aluno.id, recebida, db, agora=AGORA)
        assert _vias(db, aluno) == [gravada]

    def test_acesso_de_outro_aluno_nao_interfere(self, db, aluno):
        outro = Student(email="bia@teste.com", nome="Bia", senha_hash="x")
        db.add(outro)
        db.commit()
        registrar_acesso(outro.id, None, db, agora=AGORA)
        assert registrar_acesso(aluno.id, None, db, agora=AGORA + timedelta(minutes=1)) is True


class TestRota:
    def test_aluno_registra_e_recebe_204(self, client, db, aluno):
        resp = client.post("/aluno/acessos", json={"via": "convite"},
                           headers=_auth(create_student_token(aluno.id)))
        assert resp.status_code == 204
        assert _vias(db, aluno) == ["convite"]

    def test_corpo_vazio_grava_sem_origem(self, client, db, aluno):
        resp = client.post("/aluno/acessos", json={},
                           headers=_auth(create_student_token(aluno.id)))
        assert resp.status_code == 204
        assert _vias(db, aluno) == [None]

    def test_sem_token_da_401(self, client):
        assert client.post("/aluno/acessos", json={}).status_code == 401

    def test_token_de_professor_da_401(self, client, professor):
        resp = client.post("/aluno/acessos", json={},
                           headers=_auth(create_access_token(professor.id)))
        assert resp.status_code == 401

    def test_via_com_33_caracteres_da_422(self, client, aluno):
        resp = client.post("/aluno/acessos", json={"via": "x" * 33},
                           headers=_auth(create_student_token(aluno.id)))
        assert resp.status_code == 422
