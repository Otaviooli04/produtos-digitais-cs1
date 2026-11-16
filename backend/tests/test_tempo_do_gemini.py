import json
from unittest.mock import MagicMock, patch

import pytest

from app.llm import cliente, exercise_generator, feedback_generator, student_explainer
from app.engine import semantic_extractor
from tests.conftest import gemini_response
from tests.test_ajuda_em_etapas import ETAPAS_OK
from tests.test_insights import _seed_cluster


def _cliente_que_responde(texto):
    c = MagicMock()
    c.models.generate_content.return_value = gemini_response(texto)
    return c


def _tempo_pedido(construtor):
    opcoes = construtor.call_args.kwargs["http_options"]
    return opcoes.timeout


@pytest.fixture()
def com_chave(monkeypatch):
    for modulo in (exercise_generator, feedback_generator, student_explainer, semantic_extractor):
        monkeypatch.setattr(modulo, "GEMINI_API_KEY", "chave-de-teste")


class TestTempoLimite:
    def test_dica_do_aluno(self, com_chave):
        resposta = _cliente_que_responde(json.dumps(ETAPAS_OK))
        with patch("google.genai.Client", return_value=resposta) as c:
            student_explainer.generate_student_help("enunciado", "int main(){}", "Saída Incorreta", "diag")
        assert _tempo_pedido(c) == cliente.TEMPO_PADRAO_S * 1000

    def test_exercicio_da_trilha(self, com_chave):
        with patch("google.genai.Client", return_value=_cliente_que_responde("{}")) as c:
            with pytest.raises(exercise_generator.ExercicioInvalido):
                exercise_generator.gerar_exercicio("Saída Incorreta", "diag", [])
        assert _tempo_pedido(c) == cliente.TEMPO_PADRAO_S * 1000

    def test_insights_do_professor(self, com_chave):
        with patch("google.genai.Client", return_value=_cliente_que_responde("[]")) as c:
            feedback_generator.generate_cluster_insights("enunciado", [{
                "cluster_id": 0, "size": 2, "dominant_error": "Saída Incorreta",
                "representative_code": "int main(){}",
            }])
        assert _tempo_pedido(c) == cliente.TEMPO_PADRAO_S * 1000

    def test_extracao_da_prova_tem_mais_folga(self, com_chave):
        with patch("google.genai.Client",
                   return_value=_cliente_que_responde('{"questions": []}')) as c:
            semantic_extractor.extract_exam_structure("Questão 1: some dois números.")
        assert _tempo_pedido(c) == cliente.TEMPO_DA_EXTRACAO_S * 1000
        assert cliente.TEMPO_DA_EXTRACAO_S > cliente.TEMPO_PADRAO_S


class TestFalhaVaiParaOProfessorComoMensagem:
    def test_insights_que_estouram_o_tempo_viram_503(
        self, client, exam_factory, submission_factory, db, com_chave
    ):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        _seed_cluster(db, q.id, submission_factory(q.id).id)
        travado = MagicMock()
        travado.models.generate_content.side_effect = TimeoutError("read timeout")

        with patch("google.genai.Client", return_value=travado):
            resp = client.post(f"/exam/{exam.id}/questions/1/insights")

        assert resp.status_code == 503
        assert resp.json()["detail"]
