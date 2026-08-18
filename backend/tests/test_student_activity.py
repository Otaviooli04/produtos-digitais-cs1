"""Atividades do aluno: lista, submissão autenticada com histórico de tentativas,
regras de disponibilidade (modo, janela e teto) e os painéis de progresso e de
erros recorrentes."""
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.orm import Submission, Turma
from tests.conftest import gemini_response, make_subprocess_result

CADASTRO = {
    "email": "aluno@teste.com",
    "nome": "Aluno Teste",
    "matricula": "2026001",
    "senha": "senha-forte",
}

CODE = '#include <stdio.h>\nint main(){ printf("par\\n"); return 0; }'


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _patch_docker(*run_results):
    return patch(
        "app.engine.dynamic_analyzer.subprocess.run",
        side_effect=list(run_results),
    )


def _submeter(client, token, exam_id, numero="1", saida="par", code=CODE):
    """Uma submissão com o Docker simulado: compilação ok e uma execução."""
    with _patch_docker(make_subprocess_result(returncode=0),
                       make_subprocess_result(stdout=saida)):
        return client.post(
            f"/aluno/atividades/{exam_id}/questoes/{numero}/submissoes",
            json={"code": code},
            headers=_auth(token),
        )


@pytest.fixture()
def prova(db, exam_factory):
    """Prova de duas questões, cada uma com um caso de teste, em turma com código."""
    from app.models.orm import TestCase

    exam = exam_factory(questions=[{"number": "1"}, {"number": "2"}])
    for q in exam.questions:
        db.add(TestCase(question_id=q.id, input="2", expected_output="par"))
    turma = db.get(Turma, exam.turma_id)
    turma.codigo_acesso = "ABC234"
    db.commit()
    db.refresh(exam)
    return exam


@pytest.fixture()
def token(client, prova):
    resp = client.post("/aluno/register", json=CADASTRO)
    tok = resp.json()["access_token"]
    client.post("/aluno/turmas/entrar", json={"codigo_acesso": "ABC234"}, headers=_auth(tok))
    return tok


@pytest.fixture()
def tentativa_factory(db, prova):
    """Grava tentativas direto no banco, para montar histórico sem passar pelo Docker."""
    contador = {}

    def _create(student_id, numero="1", categoria="Correto", quando=None):
        question = next(q for q in prova.questions if q.number == numero)
        chave = (student_id, question.id)
        contador[chave] = contador.get(chave, 0) + 1
        sub = Submission(
            question_id=question.id,
            code=CODE,
            compile_error="",
            warnings="",
            all_tests_passed=(categoria == "Correto"),
            error_category=categoria,
            pedagogical_diagnosis="diagnóstico",
            actionable_feedback="o que fazer",
            student_id=student_id,
            matricula="2026001",
            attempt_number=contador[chave],
            submitted_at=quando or datetime.utcnow(),
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub
    return _create


def _aluno_id(client, token):
    return client.get("/aluno/me", headers=_auth(token)).json()["id"]


class TestListaDeAtividades:
    def test_sem_turma_nao_ve_atividade(self, client, prova):
        tok = client.post("/aluno/register", json=CADASTRO).json()["access_token"]
        assert client.get("/aluno/atividades", headers=_auth(tok)).json() == []

    def test_lista_atividades_da_turma(self, client, token, prova):
        resp = client.get("/aluno/atividades", headers=_auth(token))
        assert resp.status_code == 200
        (atividade,) = resp.json()
        assert atividade["exam_id"] == prova.id
        assert atividade["total_questoes"] == 2
        assert atividade["questoes_resolvidas"] == 0
        assert atividade["situacao"] == "aberta"
        assert atividade["modo"] == "prova"

    def test_filtra_por_turma_alheia(self, client, token, exam_factory):
        outra = exam_factory(questions=[{"number": "1"}])
        resp = client.get(
            "/aluno/atividades", params={"turma_id": outra.turma_id}, headers=_auth(token))
        assert resp.status_code == 404

    def test_detalhe_traz_questoes_e_status(self, client, token, prova):
        resp = client.get(f"/aluno/atividades/{prova.id}", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert [q["number"] for q in data["questoes"]] == ["1", "2"]
        assert data["questoes"][0]["tentativas"] == 0
        assert data["questoes"][0]["tentativas_restantes"] is None

    def test_detalhe_de_atividade_fora_das_turmas(self, client, token, exam_factory):
        outra = exam_factory(questions=[{"number": "1"}])
        assert client.get(
            f"/aluno/atividades/{outra.id}", headers=_auth(token)).status_code == 404


class TestSubmissaoAutenticada:
    def test_liga_a_conta_e_numera_a_tentativa(self, client, db, token, prova):
        primeira = _submeter(client, token, prova.id, saida="errado")
        assert primeira.status_code == 201
        assert primeira.json()["tentativa"]["attempt_number"] == 1
        assert primeira.json()["resolvida"] is False

        segunda = _submeter(client, token, prova.id, saida="par")
        assert segunda.json()["tentativa"]["attempt_number"] == 2
        assert segunda.json()["resolvida"] is True
        assert segunda.json()["tentativa"]["error_category"] == "Correto"

        subs = db.query(Submission).order_by(Submission.attempt_number).all()
        assert [s.attempt_number for s in subs] == [1, 2]
        assert all(s.student_id is not None for s in subs)
        assert all(s.matricula == "2026001" for s in subs)

    def test_tentativa_anterior_continua_no_historico(self, client, db, token, prova):
        _submeter(client, token, prova.id, saida="errado")
        _submeter(client, token, prova.id, saida="par")
        assert db.query(Submission).count() == 2

    def test_questao_inexistente(self, client, token, prova):
        resp = _submeter(client, token, prova.id, numero="99")
        assert resp.status_code == 404

    def test_codigo_vazio(self, client, token, prova):
        resp = client.post(
            f"/aluno/atividades/{prova.id}/questoes/1/submissoes",
            json={"code": "   "},
            headers=_auth(token),
        )
        assert resp.status_code == 400

    def test_atividade_de_outra_turma(self, client, token, exam_factory):
        outra = exam_factory(questions=[{"number": "1"}])
        assert _submeter(client, token, outra.id).status_code == 404

    def test_resolvida_aparece_no_detalhe(self, client, token, prova):
        _submeter(client, token, prova.id, saida="par")
        data = client.get(f"/aluno/atividades/{prova.id}", headers=_auth(token)).json()
        assert data["questoes_resolvidas"] == 1
        assert data["questoes"][0]["resolvida"] is True
        assert data["questoes"][0]["ultimo_codigo"] == CODE


class TestDisponibilidade:
    def test_atividade_ainda_nao_aberta(self, client, db, token, prova):
        prova.abre_em = datetime.utcnow() + timedelta(days=1)
        db.commit()
        resp = _submeter(client, token, prova.id)
        assert resp.status_code == 403
        assert "não abriu" in resp.json()["detail"]

    def test_atividade_encerrada(self, client, db, token, prova):
        prova.fecha_em = datetime.utcnow() - timedelta(hours=1)
        db.commit()
        resp = _submeter(client, token, prova.id)
        assert resp.status_code == 403
        assert "encerrou" in resp.json()["detail"]

    def test_teto_de_tentativas(self, client, db, token, prova):
        prova.max_tentativas = 2
        db.commit()
        assert _submeter(client, token, prova.id, saida="errado").status_code == 201
        segunda = _submeter(client, token, prova.id, saida="errado")
        assert segunda.json()["tentativas_restantes"] == 0
        terceira = _submeter(client, token, prova.id, saida="errado")
        assert terceira.status_code == 403

    def test_teto_vale_por_questao(self, client, db, token, prova):
        prova.max_tentativas = 1
        db.commit()
        assert _submeter(client, token, prova.id, numero="1", saida="errado").status_code == 201
        assert _submeter(client, token, prova.id, numero="2", saida="errado").status_code == 201

    def test_treino_nao_tem_teto(self, client, db, token, prova):
        prova.modo = "treino"
        db.commit()
        for _ in range(3):
            assert _submeter(client, token, prova.id, saida="errado").status_code == 201
        atividade = client.get("/aluno/atividades", headers=_auth(token)).json()[0]
        assert atividade["modo"] == "treino"
        assert atividade["tentativas"] == 3

    def test_situacao_agendada_na_lista(self, client, db, token, prova):
        prova.abre_em = datetime.utcnow() + timedelta(days=2)
        db.commit()
        atividade = client.get("/aluno/atividades", headers=_auth(token)).json()[0]
        assert atividade["situacao"] == "agendada"
        assert atividade["aberta"] is False


class TestHistorico:
    def test_tentativas_mais_recentes_primeiro(self, client, token, prova):
        _submeter(client, token, prova.id, saida="errado")
        _submeter(client, token, prova.id, saida="par")
        resp = client.get(
            f"/aluno/atividades/{prova.id}/questoes/1/tentativas", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["resolvida"] is True
        assert [t["attempt_number"] for t in data["tentativas"]] == [2, 1]
        assert data["tentativas"][0]["pedagogical_diagnosis"]

    def test_sem_tentativas(self, client, token, prova):
        data = client.get(
            f"/aluno/atividades/{prova.id}/questoes/2/tentativas", headers=_auth(token)).json()
        assert data["tentativas"] == []
        assert data["resolvida"] is False


class TestProgresso:
    def test_contadores(self, client, token, prova, tentativa_factory):
        aluno_id = _aluno_id(client, token)
        tentativa_factory(aluno_id, "1", "Saída Incorreta")
        tentativa_factory(aluno_id, "1", "Correto")
        tentativa_factory(aluno_id, "2", "Correto")

        data = client.get("/aluno/progresso", headers=_auth(token)).json()
        assert data["total_atividades"] == 1
        assert data["total_questoes"] == 2
        assert data["questoes_resolvidas"] == 2
        assert data["atividades_concluidas"] == 1
        assert data["total_tentativas"] == 3
        # Q1 acertou na 2ª, Q2 na 1ª → média 1,5.
        assert data["tentativas_por_questao_resolvida"] == 1.5
        assert data["acertos_de_primeira"] == 1
        assert data["dias_seguidos"] == 1

    def test_evolucao_por_semana(self, client, token, prova, tentativa_factory):
        aluno_id = _aluno_id(client, token)
        tentativa_factory(aluno_id, "1", "Saída Incorreta", quando=datetime.utcnow() - timedelta(days=14))
        tentativa_factory(aluno_id, "1", "Correto")
        data = client.get("/aluno/progresso", headers=_auth(token)).json()
        assert len(data["evolucao"]) == 2
        assert sum(p["tentativas"] for p in data["evolucao"]) == 2
        assert sum(p["resolvidas"] for p in data["evolucao"]) == 1

    def test_sem_submissao(self, client, token):
        data = client.get("/aluno/progresso", headers=_auth(token)).json()
        assert data["total_tentativas"] == 0
        assert data["tentativas_por_questao_resolvida"] is None
        assert data["dias_seguidos"] == 0


class TestErrosRecorrentes:
    def test_agrupa_e_ordena_por_frequencia(self, client, token, prova, tentativa_factory):
        aluno_id = _aluno_id(client, token)
        for _ in range(3):
            tentativa_factory(aluno_id, "1", "Laço Infinito")
        tentativa_factory(aluno_id, "2", "Saída Incorreta")
        tentativa_factory(aluno_id, "2", "Correto")

        data = client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()
        assert data["total_submissoes"] == 5
        assert data["total_com_erro"] == 4
        assert [e["error_category"] for e in data["erros"]] == ["Laço Infinito", "Saída Incorreta"]
        assert data["erros"][0]["total"] == 3
        assert data["erros"][0]["o_que_fazer"] == "o que fazer"
        assert data["erros"][0]["questoes"]

    def test_acerto_nao_entra_no_painel(self, client, token, prova, tentativa_factory):
        aluno_id = _aluno_id(client, token)
        tentativa_factory(aluno_id, "1", "Correto")
        data = client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()
        assert data["erros"] == []

    def test_erro_antigo_que_parou_de_acontecer_esta_melhorando(
        self, client, token, prova, tentativa_factory,
    ):
        aluno_id = _aluno_id(client, token)
        antigo = datetime.utcnow() - timedelta(days=30)
        for _ in range(4):
            tentativa_factory(aluno_id, "1", "Laço Infinito", quando=antigo)
        for _ in range(10):
            tentativa_factory(aluno_id, "2", "Saída Incorreta")

        erros = {e["error_category"]: e for e in
                 client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()["erros"]}
        assert erros["Laço Infinito"]["tendencia"] == "melhorando"
        assert erros["Laço Infinito"]["recentes"] == 0
        assert erros["Saída Incorreta"]["tendencia"] == "piorando"


class TestExplicacaoIndividual:
    """A LLM traduz o erro para quem o cometeu. Uma geração por tentativa."""

    def _mock_gemini(self, texto="Você compara o resto da divisão errado."):
        client = MagicMock()
        client.models.generate_content.return_value = gemini_response(texto)
        return client

    def test_gera_uma_vez_e_reaproveita(self, client, token, prova):
        sub_id = _submeter(client, token, prova.id, saida="errado").json()["tentativa"]["submission_id"]
        mock = self._mock_gemini()

        with patch("app.llm.student_explainer.genai.Client", return_value=mock):
            primeira = client.post(f"/aluno/tentativas/{sub_id}/explicacao", headers=_auth(token))
            segunda = client.post(f"/aluno/tentativas/{sub_id}/explicacao", headers=_auth(token))

        assert primeira.status_code == 200
        assert primeira.json()["gerada_agora"] is True
        assert primeira.json()["explicacao"].startswith("Você compara")
        assert segunda.json()["gerada_agora"] is False
        # Segunda chamada sai do cache: o modelo é chamado uma única vez.
        assert mock.models.generate_content.call_count == 1

    def test_explicacao_acompanha_a_tentativa_no_historico(self, client, token, prova):
        sub_id = _submeter(client, token, prova.id, saida="errado").json()["tentativa"]["submission_id"]
        with patch("app.llm.student_explainer.genai.Client", return_value=self._mock_gemini()):
            client.post(f"/aluno/tentativas/{sub_id}/explicacao", headers=_auth(token))

        historico = client.get(
            f"/aluno/atividades/{prova.id}/questoes/1/tentativas", headers=_auth(token)).json()
        assert historico["tentativas"][0]["explicacao"].startswith("Você compara")

    def test_tentativa_correta_nao_gasta_chamada(self, client, token, prova):
        sub_id = _submeter(client, token, prova.id, saida="par").json()["tentativa"]["submission_id"]
        resp = client.post(f"/aluno/tentativas/{sub_id}/explicacao", headers=_auth(token))
        assert resp.status_code == 400

    def test_tentativa_de_outro_aluno(self, client, db, token, prova, tentativa_factory):
        from app.models.orm import Student

        outro = Student(email="outro@teste.com", nome="Outro", senha_hash="x")
        db.add(outro)
        db.commit()
        alheia = tentativa_factory(outro.id, "1", "Saída Incorreta")
        resp = client.post(f"/aluno/tentativas/{alheia.id}/explicacao", headers=_auth(token))
        assert resp.status_code == 404
