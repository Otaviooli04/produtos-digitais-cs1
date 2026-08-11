import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock

import psycopg2
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import urlparse, urlunparse

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

from app.main import app as fastapi_app
from app.auth.dependencies import get_current_professor
from app.models.database import Base, get_db
from app.models.orm import Exam, Professor, Question, QuestionCluster, Submission, TestCase, Turma
import app.models.orm  # registra todos os modelos no metadata

_parsed_url = urlparse(os.environ["DATABASE_URL"])
_test_db_name = _parsed_url.path.lstrip("/") + "_test"
TEST_DATABASE_URL = urlunparse(_parsed_url._replace(path=f"/{_test_db_name}"))


def _ensure_test_db_exists():
    try:
        conn = psycopg2.connect(TEST_DATABASE_URL)
        conn.close()
    except psycopg2.OperationalError:
        raise RuntimeError(
            f"Banco de teste '{_test_db_name}' não encontrado. "
            f"Crie-o com: createdb {_test_db_name}"
        )


_ensure_test_db_exists()

engine = create_engine(TEST_DATABASE_URL)
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db():
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def clean_tables(db):
    yield
    db.rollback()
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()


@pytest.fixture()
def professor(db):
    prof = Professor(email="prof@teste.com", nome="Professor Teste", senha_hash="x")
    db.add(prof)
    db.commit()
    db.refresh(prof)
    return prof


@pytest.fixture()
def client(db, professor):
    def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_professor] = lambda: professor
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def run_jobs_sync(db, monkeypatch):
    """Executa os jobs de segundo plano de forma síncrona na sessão de teste.

    Em produção `run_in_background` dispara uma thread com sessão própria (banco
    de produção). Nos testes substituímos por execução síncrona no banco de teste,
    espelhando o tratamento de erro real (status 'error' em vez de propagar)."""
    from app.services.job_service import update_job

    def _sync(job_id, target):
        update_job(db, job_id, status="running")
        try:
            target(db, job_id)
        except Exception as e:  # noqa: BLE001 — reportado no status do job
            update_job(db, job_id, status="error", message=str(e))

    monkeypatch.setattr("app.services.exam_service.run_in_background", _sync)
    monkeypatch.setattr(
        "app.services.bulk_submission_service.run_in_background", _sync, raising=False)
    return _sync


# --- factories ---

@pytest.fixture()
def exam_factory(db, professor):
    def _create(filename="prova.pdf", questions=None):
        turma = Turma(nome="Turma Teste", codigo="TT", professor_id=professor.id)
        db.add(turma)
        db.flush()
        exam = Exam(filename=filename, raw_text="texto da prova",
                    created_at=datetime.now(timezone.utc), turma_id=turma.id)
        db.add(exam)
        db.flush()
        for q in (questions or []):
            question = Question(
                exam_id=exam.id,
                number=q.get("number", "1"),
                statement=q.get("statement", "Enunciado padrão"),
                required_structures=q.get("required_structures", []),
                forbidden_structures=q.get("forbidden_structures", []),
                requires_loop=q.get("requires_loop", False),
            )
            db.add(question)
        db.commit()
        db.refresh(exam)
        return exam
    return _create


@pytest.fixture()
def submission_factory(db):
    def _create(question_id, code="int main(){return 0;}", error_category="Correto",
                all_tests_passed=True, ast_structures=None):
        sub = Submission(
            question_id=question_id,
            code=code,
            compile_error="",
            warnings="",
            all_tests_passed=all_tests_passed,
            error_category=error_category,
            pedagogical_diagnosis="",
            actionable_feedback="",
            ast_structures=ast_structures or ["If"],
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub
    return _create


# --- mocks reutilizáveis ---

def make_subprocess_result(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


def gemini_response(text: str):
    m = MagicMock()
    m.text = text
    return m
