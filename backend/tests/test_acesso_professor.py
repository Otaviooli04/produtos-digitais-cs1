"""Quem pode chamar as rotas do professor: só o professor dono da atividade, com
token de professor. Cobre o token do aluno, assinado com a mesma chave, e as duas
rotas herdadas do TCC que ficavam abertas."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.auth.service import create_access_token
from app.auth.student_service import create_student_token
from app.core.config import JWT_ALGORITHM, SECRET_KEY
from app.main import app as fastapi_app
from app.models.database import get_db
from app.models.orm import Exam, Professor, Submission


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def anonimo(db):
    """Cliente sem professor injetado: quem decide é a autenticação de verdade."""
    def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def outro_professor(db):
    prof = Professor(email="outro@teste.com", nome="Outro Professor", senha_hash="x")
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof


def _envio(exam, dry_run=False):
    return {"exam_id": exam.id, "question_number": "1",
            "code": "int main(){return 0;}", "dry_run": dry_run}


class TestTokenDoProfessor:
    def test_token_de_aluno_nao_vale_como_professor(self, anonimo, professor):
        """Aluno e professor ficam em tabelas diferentes, cada uma com sua sequência
        de id. Sem conferir o papel, o aluno de id N entrava como o professor de id N."""
        token = create_student_token(professor.id)
        assert anonimo.get("/turmas", headers=_auth(token)).status_code == 401

    def test_token_sem_papel_nao_vale(self, anonimo, professor):
        expira = datetime.now(timezone.utc) + timedelta(hours=1)
        token = jwt.encode({"sub": str(professor.id), "exp": expira}, SECRET_KEY, algorithm=JWT_ALGORITHM)
        assert anonimo.get("/turmas", headers=_auth(token)).status_code == 401

    def test_token_de_professor_continua_valendo(self, anonimo, professor):
        assert anonimo.get("/turmas", headers=_auth(create_access_token(professor.id))).status_code == 200


class TestAvaliarCodigo:
    def test_exige_login(self, anonimo, exam_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        assert anonimo.post("/submission/evaluate", json=_envio(exam, dry_run=True)).status_code == 401

    def test_atividade_de_outro_professor_nao_roda_nem_grava(
        self, anonimo, exam_factory, outro_professor, db
    ):
        exam = exam_factory(questions=[{"number": "1"}])
        with patch("app.engine.dynamic_analyzer.subprocess.run") as docker:
            resp = anonimo.post("/submission/evaluate", json=_envio(exam),
                                headers=_auth(create_access_token(outro_professor.id)))
        assert resp.status_code == 404
        docker.assert_not_called()
        assert db.query(Submission).count() == 0


class TestVerAtividade:
    def test_exige_login(self, anonimo, exam_factory):
        exam = exam_factory()
        assert anonimo.get(f"/exam/{exam.id}").status_code == 401

    def test_atividade_de_outro_professor(self, anonimo, exam_factory, outro_professor):
        exam = exam_factory()
        resp = anonimo.get(f"/exam/{exam.id}", headers=_auth(create_access_token(outro_professor.id)))
        assert resp.status_code == 404

    def test_dono_ve_a_atividade(self, anonimo, exam_factory, professor):
        exam = exam_factory(titulo="Lista 1")
        resp = anonimo.get(f"/exam/{exam.id}", headers=_auth(create_access_token(professor.id)))
        assert resp.status_code == 200
        assert resp.json()["titulo"] == "Lista 1"

    def test_atividade_antiga_sem_turma_nao_tem_dono(self, anonimo, db, professor):
        exam = Exam(filename="prova_tcc.pdf", raw_text="texto")
        db.add(exam)
        db.commit()
        resp = anonimo.get(f"/exam/{exam.id}", headers=_auth(create_access_token(professor.id)))
        assert resp.status_code == 404
