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


class TestPublicacaoDaAtividade:
    """O portão entre a atividade montada e a atividade visível para o aluno.
    Antes dele, subir o PDF já colocava a prova na tela do aluno, com as questões
    que o extrator tinha acabado de produzir."""

    def test_rascunho_nao_aparece_na_lista(self, client, token, prova, db):
        prova.publicada = False
        db.commit()
        assert client.get("/aluno/atividades", headers=_auth(token)).json() == []

    def test_rascunho_nao_abre_nem_por_id(self, client, token, prova, db):
        prova.publicada = False
        db.commit()
        resp = client.get(f"/aluno/atividades/{prova.id}", headers=_auth(token))
        assert resp.status_code == 404

    def test_rascunho_nao_aceita_submissao(self, client, token, prova, db):
        prova.publicada = False
        db.commit()
        resp = client.post(
            f"/aluno/atividades/{prova.id}/questoes/1/submissoes",
            json={"code": "int main(){return 0;}"},
            headers=_auth(token),
        )
        assert resp.status_code == 404

    def test_publicar_devolve_a_atividade_ao_aluno(self, client, token, prova, db):
        prova.publicada = False
        db.commit()
        assert client.get("/aluno/atividades", headers=_auth(token)).json() == []
        prova.publicada = True
        db.commit()
        (atividade,) = client.get("/aluno/atividades", headers=_auth(token)).json()
        assert atividade["exam_id"] == prova.id


class TestTituloDaAtividade:
    def test_sem_titulo_cai_no_nome_do_arquivo(self, client, token, prova):
        (atividade,) = client.get("/aluno/atividades", headers=_auth(token)).json()
        assert atividade["titulo"] == "prova.pdf"

    def test_titulo_definido_vence_o_nome_do_arquivo(self, client, token, prova, db):
        prova.titulo = "Lista 3 · Vetores e laços"
        db.commit()
        (atividade,) = client.get("/aluno/atividades", headers=_auth(token)).json()
        assert atividade["titulo"] == "Lista 3 · Vetores e laços"

    def test_titulo_aparece_no_painel_de_erros_recorrentes(
        self, client, token, prova, tentativa_factory, db
    ):
        prova.titulo = "Lista 3"
        db.commit()
        tentativa_factory(_aluno_id(client, token), categoria="Acesso Fora dos Limites: Off-by-One")
        data = client.get("/aluno/erros-recorrentes", headers=_auth(token)).json()
        assert data["erros"][0]["questoes"] == ["Lista 3 · Q1"]


class TestAgrupamentoNoEnvioDoAluno:
    """Antes disso o agrupamento só rodava no lote ou no botão do professor, e no
    fluxo real da turma, em que o aluno envia um a um, nenhum dos dois disparava."""

    def _envia(self, client, token, prova, codigo, monkeypatch, categoria="Saída Incorreta"):
        from app.services import student_activity_service as svc

        monkeypatch.setattr(svc, "evaluate_code", lambda *a, **k: {
            "compile_error": "",
            "warnings": "",
            "all_tests_passed": categoria == "Correto",
            "diagnosis": {
                "error_category": categoria,
                "pedagogical_diagnosis": "diagnóstico",
                "actionable_feedback": "o que fazer",
            },
            "ast_structures": [],
            "ast_functions": [],
            "test_results": [],
        })
        return client.post(
            f"/aluno/atividades/{prova.id}/questoes/1/submissoes",
            json={"code": codigo},
            headers=_auth(token),
        )

    def test_grupo_existe_sem_ninguem_apertar_botao(
        self, client, token, prova, db, monkeypatch, submission_factory
    ):
        from app.models.orm import QuestionCluster

        questao = next(q for q in prova.questions if q.number == "1")
        # Duas submissões antigas, para cruzar o mínimo de agrupamento no envio.
        submission_factory(questao.id, code="int main(){return 1;}",
                           error_category="Saída Incorreta", all_tests_passed=False)
        submission_factory(questao.id, code="int main(){return 2;}",
                           error_category="Saída Incorreta", all_tests_passed=False)

        resp = self._envia(client, token, prova, "int main(){return 3;}", monkeypatch)
        assert resp.status_code == 201

        db.expire_all()
        grupos = db.query(QuestionCluster).filter(
            QuestionCluster.question_id == questao.id).all()
        assert grupos, "o envio do aluno precisa formar o grupo sozinho"
        assert all(g.chave for g in grupos)
        assert all(g.atualizado_em for g in grupos)

    def test_agrupar_nao_apaga_o_insight_do_professor(
        self, client, token, prova, db, monkeypatch, submission_factory
    ):
        """Re-agrupar apagava as linhas e levava junto o que estava escrito nelas."""
        from app.models.orm import QuestionCluster

        questao = next(q for q in prova.questions if q.number == "1")
        for i in range(3):
            submission_factory(questao.id, code=f"int main(){{return {i};}}",
                               error_category="Saída Incorreta", all_tests_passed=False)

        from app.ml.cluster import atribuir_grupos
        atribuir_grupos(questao.id, db)
        grupo = db.query(QuestionCluster).filter(
            QuestionCluster.question_id == questao.id).first()
        grupo.insight = "Este grupo confundiu a condição de parada."
        db.commit()
        chave = grupo.chave

        self._envia(client, token, prova, "int main(){return 9;}", monkeypatch)

        db.expire_all()
        depois = db.query(QuestionCluster).filter(
            QuestionCluster.question_id == questao.id,
            QuestionCluster.chave == chave).first()
        assert depois is not None
        assert depois.insight == "Este grupo confundiu a condição de parada."

    def test_falha_no_agrupamento_nao_derruba_a_submissao(
        self, client, token, prova, monkeypatch, submission_factory
    ):
        questao = next(q for q in prova.questions if q.number == "1")
        for i in range(3):
            submission_factory(questao.id, code=f"int main(){{return {i};}}",
                               error_category="Saída Incorreta", all_tests_passed=False)

        import app.ml.cluster as cluster_mod

        def explode(*a, **k):
            raise RuntimeError("agrupamento quebrou")

        monkeypatch.setattr(cluster_mod, "atribuir_grupos", explode)
        resp = self._envia(client, token, prova, "int main(){return 9;}", monkeypatch)
        assert resp.status_code == 201
        assert resp.json()["tentativa"]["error_category"] == "Saída Incorreta"


class TestRetornoDoProfessorAoGrupo:
    """O professor escreve uma vez e o texto chega a todo mundo que errou do
    mesmo jeito. Era o passo 4 da jornada dele, e não existia."""

    def _prepara_grupo(self, db, prova, submission_factory, quantos=3):
        from app.ml.cluster import atribuir_grupos
        from app.models.orm import QuestionCluster

        questao = next(q for q in prova.questions if q.number == "1")
        for i in range(quantos):
            submission_factory(questao.id, code=f"int main(){{return {i};}}",
                               error_category="Saída Incorreta", all_tests_passed=False)
        atribuir_grupos(questao.id, db)
        grupo = db.query(QuestionCluster).filter(
            QuestionCluster.question_id == questao.id).first()
        return questao, grupo

    def test_professor_salva_e_o_grupo_guarda(
        self, client, prova, db, submission_factory
    ):
        from app.models.orm import QuestionCluster

        questao, grupo = self._prepara_grupo(db, prova, submission_factory)
        resp = client.put(
            f"/exam/{prova.id}/questions/1/grupos/{grupo.cluster_label}/resposta",
            json={"texto": "Revejam a condição de parada do laço."},
        )
        assert resp.status_code == 200
        assert resp.json()["resposta_professor"] == "Revejam a condição de parada do laço."

        db.expire_all()
        salvo = db.get(QuestionCluster, grupo.id)
        assert salvo.resposta_professor == "Revejam a condição de parada do laço."
        assert salvo.resposta_em is not None
        assert salvo.resposta_por is not None

    def test_texto_vazio_apaga_a_resposta(self, client, prova, db, submission_factory):
        from app.models.orm import QuestionCluster

        questao, grupo = self._prepara_grupo(db, prova, submission_factory)
        client.put(f"/exam/{prova.id}/questions/1/grupos/{grupo.cluster_label}/resposta",
                   json={"texto": "texto qualquer"})
        client.put(f"/exam/{prova.id}/questions/1/grupos/{grupo.cluster_label}/resposta",
                   json={"texto": "   "})
        db.expire_all()
        assert db.get(QuestionCluster, grupo.id).resposta_professor is None

    def test_grupo_inexistente_devolve_404(self, client, prova, db, submission_factory):
        self._prepara_grupo(db, prova, submission_factory)
        resp = client.put(f"/exam/{prova.id}/questions/1/grupos/999/resposta",
                          json={"texto": "oi"})
        assert resp.status_code == 404

    def test_resposta_chega_na_tentativa_do_aluno(
        self, client, token, prova, db, tentativa_factory, submission_factory
    ):
        from app.ml.cluster import atribuir_grupos
        from app.models.orm import QuestionCluster

        questao = next(q for q in prova.questions if q.number == "1")
        for i in range(2):
            submission_factory(questao.id, code=f"int main(){{return {i};}}",
                               error_category="Saída Incorreta", all_tests_passed=False)
        minha = tentativa_factory(_aluno_id(client, token), categoria="Saída Incorreta")
        atribuir_grupos(questao.id, db)
        db.expire_all()

        grupo = db.query(QuestionCluster).filter(
            QuestionCluster.question_id == questao.id,
            QuestionCluster.cluster_label == db.get(Submission, minha.id).cluster_id,
        ).first()
        client.put(f"/exam/{prova.id}/questions/1/grupos/{grupo.cluster_label}/resposta",
                   json={"texto": "Vale rever a condição de parada."})

        data = client.get(
            f"/aluno/atividades/{prova.id}/questoes/1/tentativas", headers=_auth(token)).json()
        assert data["tentativas"][0]["resposta_do_professor"] == "Vale rever a condição de parada."

    def test_aluno_de_outro_grupo_nao_recebe(
        self, client, token, prova, db, tentativa_factory, submission_factory
    ):
        from app.ml.cluster import atribuir_grupos
        from app.models.orm import QuestionCluster

        questao = next(q for q in prova.questions if q.number == "1")
        for i in range(2):
            submission_factory(questao.id, code=f"int main(){{return {i};}}",
                               error_category="Saída Incorreta", all_tests_passed=False)
        # O aluno erra de outro jeito, então cai em outro grupo.
        tentativa_factory(_aluno_id(client, token), categoria="Tudo no Main")
        atribuir_grupos(questao.id, db)
        db.expire_all()

        outro = db.query(QuestionCluster).filter(
            QuestionCluster.question_id == questao.id,
            QuestionCluster.dominant_error == "Saída Incorreta",
        ).first()
        client.put(f"/exam/{prova.id}/questions/1/grupos/{outro.cluster_label}/resposta",
                   json={"texto": "Só para quem errou a saída."})

        data = client.get(
            f"/aluno/atividades/{prova.id}/questoes/1/tentativas", headers=_auth(token)).json()
        assert data["tentativas"][0]["resposta_do_professor"] is None

    def test_resposta_sobrevive_ao_reagrupamento(
        self, client, prova, db, submission_factory
    ):
        """O risco que a chave estável existe para evitar: re-agrupar renumera os
        rótulos, e a resposta não pode migrar de grupo nem sumir."""
        from app.ml.cluster import atribuir_grupos
        from app.models.orm import QuestionCluster

        questao, grupo = self._prepara_grupo(db, prova, submission_factory)
        client.put(f"/exam/{prova.id}/questions/1/grupos/{grupo.cluster_label}/resposta",
                   json={"texto": "Revejam a condição de parada."})
        chave = grupo.chave

        # Chega gente errando de outro jeito, o que muda a numeração dos grupos.
        for i in range(4):
            submission_factory(questao.id, code=f"int x{i}(){{return {i};}}",
                               error_category="Tudo no Main", all_tests_passed=False)
        atribuir_grupos(questao.id, db)

        db.expire_all()
        depois = db.query(QuestionCluster).filter(
            QuestionCluster.question_id == questao.id,
            QuestionCluster.chave == chave).first()
        assert depois is not None
        assert depois.resposta_professor == "Revejam a condição de parada."
