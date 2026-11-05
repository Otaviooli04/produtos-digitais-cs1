"""Fase 0 de segurança: segredo obrigatório, senha mínima, limites de upload e
do zip, e o contêiner do C com limites e usuário sem root."""
import io
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.engine import dynamic_analyzer
from app.services import bulk_submission_service
from tests.conftest import make_subprocess_result

BACKEND = Path(__file__).resolve().parents[1]


def test_backend_recusa_subir_sem_secret_key():
    env = {**os.environ, "SECRET_KEY": ""}
    r = subprocess.run([sys.executable, "-c", "import app.core.config"],
                       cwd=BACKEND, env=env, capture_output=True, text=True)
    assert r.returncode != 0
    assert "SECRET_KEY não definido" in r.stderr


class TestSenhaMinima:
    def test_cadastro_do_aluno_recusa_senha_curta(self, client):
        resp = client.post("/aluno/register", json={
            "email": "curta@teste.com", "nome": "Curta", "matricula": "1", "senha": "1234567"})
        assert resp.status_code == 422

    def test_cadastro_do_professor_recusa_senha_curta(self, client):
        resp = client.post("/auth/register", json={
            "email": "prof-curta@teste.com", "nome": "Prof", "senha": "1234567"})
        assert resp.status_code == 422

    def test_oito_caracteres_bastam(self, client):
        resp = client.post("/aluno/register", json={
            "email": "oito@teste.com", "nome": "Oito", "matricula": "1", "senha": "12345678"})
        assert resp.status_code == 201

    def test_login_nao_aplica_a_regra_nova(self, client):
        resp = client.post("/aluno/login", json={"email": "ninguem@teste.com", "senha": "curta"})
        assert resp.status_code == 401


class TestLimiteDoUpload:
    def test_pdf_acima_do_limite_da_413(self, client, monkeypatch):
        from app.api.routes import exam as rotas
        monkeypatch.setattr(rotas, "LIMITE_DO_PDF", 10)
        resp = client.post("/exam/upload",
                           files={"file": ("prova.pdf", b"x" * 11, "application/pdf")})
        assert resp.status_code == 413

    def test_zip_acima_do_limite_da_413(self, client, exam_factory, monkeypatch):
        from app.api.routes import exam as rotas
        monkeypatch.setattr(rotas, "LIMITE_DO_ZIP", 10)
        exam = exam_factory(questions=[{"number": "1"}])
        resp = client.post(f"/exam/{exam.id}/submissions/bulk",
                           data={"format": "by_student"},
                           files={"file": ("envios.zip", b"x" * 11, "application/zip")})
        assert resp.status_code == 413


def _zip(arquivos: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, conteudo in arquivos.items():
            zf.writestr(nome, conteudo)
    return buf.getvalue()


class TestZipBomb:
    def test_arquivo_grande_demais_e_recusado_antes_de_ler(self):
        dados = _zip({"2026001/Q1.c": b"a" * (bulk_submission_service.MAX_BYTES_POR_ARQUIVO + 1)})
        with pytest.raises(ValueError, match="256 KB"):
            bulk_submission_service._enumerate_submissions(dados, "by_student")

    def test_arquivos_demais_sao_recusados(self, monkeypatch):
        monkeypatch.setattr(bulk_submission_service, "MAX_ARQUIVOS_NO_ZIP", 2)
        dados = _zip({f"20260{i}/Q1.c": b"int main(){}" for i in range(3)})
        with pytest.raises(ValueError, match="mais de 2"):
            bulk_submission_service._enumerate_submissions(dados, "by_student")

    def test_total_descompactado_acima_do_limite(self, monkeypatch):
        monkeypatch.setattr(bulk_submission_service, "MAX_BYTES_DESCOMPACTADOS", 20)
        dados = _zip({"2026001/Q1.c": b"a" * 15, "2026002/Q1.c": b"b" * 15})
        with pytest.raises(ValueError, match="descompactado"):
            bulk_submission_service._enumerate_submissions(dados, "by_student")

    def test_zip_normal_continua_passando(self):
        dados = _zip({"2026001/Q1.c": b"int main(){}", "2026002/Q1.c": b"int main(){}"})
        entradas = bulk_submission_service._enumerate_submissions(dados, "by_student")
        assert sorted(e["matricula"] for e in entradas) == ["2026001", "2026002"]


def test_conteiner_com_limites_usuario_sem_root_e_imagem_fixa():
    with patch("app.engine.dynamic_analyzer.subprocess.run", side_effect=[
            make_subprocess_result(returncode=0), make_subprocess_result(stdout="ok")]) as run:
        dynamic_analyzer.compile_and_run("int main(){}", [{"input": "", "expected_output": "ok"}])
    for chamada in run.call_args_list:
        cmd = chamada.args[0]
        assert "--network" in cmd and cmd[cmd.index("--network") + 1] == "none"
        assert cmd[cmd.index("--memory") + 1] == "256m"
        assert cmd[cmd.index("--pids-limit") + 1] == "64"
        assert cmd[cmd.index("--user") + 1] == f"{os.getuid()}:{os.getgid()}"
        assert "--cap-drop" in cmd
        assert dynamic_analyzer.IMAGEM_GCC in cmd
        assert "gcc:latest" not in cmd
