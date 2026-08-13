"""Auth do aluno: cadastro, login, entrada por código de turma e religação das
submissões feitas antes da conta existir."""
import pytest

from app.auth.service import create_access_token
from app.models.orm import Enrollment, Submission, Turma

CADASTRO = {
    "email": "Aluno@Teste.com",
    "nome": "Aluno Teste",
    "matricula": "2026001",
    "senha": "senha-forte",
}


def _registrar(client, **overrides):
    return client.post("/aluno/register", json={**CADASTRO, **overrides})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def turma_com_codigo(db, exam_factory):
    """Prova numa turma com código de acesso conhecido."""
    exam = exam_factory(questions=[{"number": "1"}])
    turma = db.get(Turma, exam.turma_id)
    turma.codigo_acesso = "ABC234"
    db.commit()
    return turma, exam


class TestCadastroELogin:
    def test_cadastro_devolve_token_e_normaliza_email(self, client):
        resp = _registrar(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["access_token"]
        assert data["aluno"]["email"] == "aluno@teste.com"
        assert data["aluno"]["matricula"] == "2026001"

    def test_email_duplicado_recusado(self, client):
        _registrar(client)
        resp = _registrar(client, nome="Outro")
        assert resp.status_code == 400
        assert "cadastrado" in resp.json()["detail"].lower()

    def test_login_com_senha_correta(self, client):
        _registrar(client)
        resp = client.post("/aluno/login", json={"email": "aluno@teste.com", "senha": "senha-forte"})
        assert resp.status_code == 200
        assert resp.json()["aluno"]["nome"] == "Aluno Teste"

    def test_login_com_senha_errada(self, client):
        _registrar(client)
        resp = client.post("/aluno/login", json={"email": "aluno@teste.com", "senha": "errada"})
        assert resp.status_code == 401


class TestTokenDoAluno:
    def test_me_exige_token(self, client):
        assert client.get("/aluno/me").status_code == 401

    def test_me_com_token_do_aluno(self, client):
        token = _registrar(client).json()["access_token"]
        resp = client.get("/aluno/me", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "aluno@teste.com"

    def test_token_de_professor_nao_vale_como_aluno(self, client, professor):
        """O papel no token separa os dois mundos: um JWT de professor, ainda que
        assinado com a mesma chave, não abre rota de aluno."""
        resp = client.get("/aluno/me", headers=_auth(create_access_token(professor.id)))
        assert resp.status_code == 401


class TestEntrarNaTurma:
    def test_entra_com_codigo_valido(self, client, turma_com_codigo):
        turma, _ = turma_com_codigo
        token = _registrar(client).json()["access_token"]
        resp = client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == turma.id
        assert resp.json()["professor_nome"] == "Professor Teste"

    def test_codigo_aceita_minusculo_e_espacos(self, client, turma_com_codigo):
        token = _registrar(client).json()["access_token"]
        resp = client.post("/aluno/turmas/entrar", json={"codigo_acesso": " abc234 "}, headers=_auth(token))
        assert resp.status_code == 200

    def test_codigo_invalido(self, client, turma_com_codigo):
        token = _registrar(client).json()["access_token"]
        resp = client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ZZZZZZ"}, headers=_auth(token))
        assert resp.status_code == 404

    def test_entrar_duas_vezes_nao_duplica(self, client, db, turma_com_codigo):
        turma, _ = turma_com_codigo
        token = _registrar(client).json()["access_token"]
        for _ in range(2):
            resp = client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))
            assert resp.status_code == 200
        assert db.query(Enrollment).filter_by(turma_id=turma.id).count() == 1

    def test_minhas_turmas(self, client, turma_com_codigo):
        token = _registrar(client).json()["access_token"]
        assert client.get("/aluno/turmas", headers=_auth(token)).json() == []
        client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))
        turmas = client.get("/aluno/turmas", headers=_auth(token)).json()
        assert len(turmas) == 1
        assert turmas[0]["exam_count"] == 1


class TestReligacaoDeSubmissoes:
    def test_submissoes_antigas_da_matricula_sao_religadas(
        self, client, db, turma_com_codigo, submission_factory,
    ):
        _, exam = turma_com_codigo
        antiga = submission_factory(exam.questions[0].id)
        antiga.matricula = "2026001"
        db.commit()
        assert antiga.student_id is None

        token = _registrar(client).json()["access_token"]
        client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))

        db.refresh(antiga)
        assert antiga.student_id is not None

    def test_nao_religa_submissao_de_outra_matricula(
        self, client, db, turma_com_codigo, submission_factory,
    ):
        _, exam = turma_com_codigo
        de_outro = submission_factory(exam.questions[0].id)
        de_outro.matricula = "2026999"
        db.commit()

        token = _registrar(client).json()["access_token"]
        client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))

        db.refresh(de_outro)
        assert de_outro.student_id is None

    def test_nao_religa_fora_das_turmas_do_aluno(
        self, client, db, turma_com_codigo, exam_factory, submission_factory,
    ):
        """Mesma matrícula, mas prova de outra turma em que o aluno não entrou."""
        outra_prova = exam_factory(questions=[{"number": "1"}])
        de_outra_turma = submission_factory(outra_prova.questions[0].id)
        de_outra_turma.matricula = "2026001"
        db.commit()

        token = _registrar(client).json()["access_token"]
        client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))

        db.refresh(de_outra_turma)
        assert de_outra_turma.student_id is None

    def test_aluno_sem_matricula_nao_religa_nada(
        self, client, db, turma_com_codigo, submission_factory,
    ):
        _, exam = turma_com_codigo
        orfa = submission_factory(exam.questions[0].id)
        orfa.matricula = "2026001"
        db.commit()

        token = _registrar(client, email="sem@matricula.com", matricula="").json()["access_token"]
        client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(token))

        db.refresh(orfa)
        assert orfa.student_id is None


class TestPerfilDoAluno:
    def test_atualiza_nome_e_matricula(self, client):
        token = _registrar(client).json()["access_token"]
        resp = client.put(
            "/aluno/me", json={"nome": "Nome Novo", "matricula": "2026002"}, headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["nome"] == "Nome Novo"
        assert resp.json()["matricula"] == "2026002"

    def test_troca_de_senha(self, client):
        token = _registrar(client).json()["access_token"]
        resp = client.put(
            "/aluno/me/password",
            json={"senha_atual": "senha-forte", "senha_nova": "outra-senha"},
            headers=_auth(token),
        )
        assert resp.status_code == 204
        assert client.post(
            "/aluno/login", json={"email": "aluno@teste.com", "senha": "outra-senha"}
        ).status_code == 200

    def test_troca_de_senha_com_senha_atual_errada(self, client):
        token = _registrar(client).json()["access_token"]
        resp = client.put(
            "/aluno/me/password",
            json={"senha_atual": "errada", "senha_nova": "outra-senha"},
            headers=_auth(token),
        )
        assert resp.status_code == 400
