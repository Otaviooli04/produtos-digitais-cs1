import json
from unittest.mock import MagicMock, patch

from app.models.orm import QuestionCluster
from tests.conftest import gemini_response


def _seed_cluster(db, question_id, sub_id, label=0, dominant_error="Saída Incorreta"):
    qc = QuestionCluster(
        question_id=question_id,
        cluster_label=label,
        size=2,
        dominant_error=dominant_error,
        representative_submission_id=sub_id,
    )
    db.add(qc)
    db.commit()
    return qc


def _mock_gemini_client(insights):
    """insights: dict {cluster_id: texto}. O batch devolve a lista crua em JSON."""
    payload = [{"cluster_id": cid, "insight": txt} for cid, txt in insights.items()]
    client = MagicMock()
    client.models.generate_content.return_value = gemini_response(json.dumps(payload))
    return client


class TestInsights:
    def test_sem_clusters_retorna_422(self, client, exam_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        resp = client.post(f"/exam/{exam.id}/questions/1/insights")
        assert resp.status_code == 422

    def test_questao_inexistente_retorna_404(self, client, exam_factory):
        exam = exam_factory()
        resp = client.post(f"/exam/{exam.id}/questions/99/insights")
        assert resp.status_code == 404

    def test_retorna_um_insight_por_cluster(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        sub1 = submission_factory(q.id)
        sub2 = submission_factory(q.id)
        _seed_cluster(db, q.id, sub1.id, label=0, dominant_error="Saída Incorreta")
        _seed_cluster(db, q.id, sub2.id, label=1, dominant_error="Erro de Compilação")

        with patch(
            "app.llm.feedback_generator.genai.Client",
            return_value=_mock_gemini_client({
                0: "Grupo não entendeu a saída esperada.",
                1: "Grupo não compila por falta de ponto e vírgula.",
            }),
        ):
            resp = client.post(f"/exam/{exam.id}/questions/1/insights")

        assert resp.status_code == 200
        data = resp.json()
        assert data["question_number"] == "1"
        assert len(data["insights"]) == 2

    def test_insight_contem_campos_corretos(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        sub = submission_factory(q.id)
        _seed_cluster(db, q.id, sub.id, label=0, dominant_error="Saída Incorreta")

        with patch(
            "app.llm.feedback_generator.genai.Client",
            return_value=_mock_gemini_client({0: "Alunos não trataram o caso de número negativo."}),
        ):
            resp = client.post(f"/exam/{exam.id}/questions/1/insights")

        assert resp.status_code == 200
        insight = resp.json()["insights"][0]
        assert insight["cluster_id"] == 0
        assert insight["dominant_error"] == "Saída Incorreta"
        assert insight["size"] == 2
        assert "Alunos não trataram" in insight["insight"]

    def test_segunda_chamada_usa_cache(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        sub = submission_factory(q.id)
        _seed_cluster(db, q.id, sub.id, label=0)
        mock_client = _mock_gemini_client({0: "Insight do Gemini."})

        with patch("app.llm.feedback_generator.genai.Client", return_value=mock_client):
            r1 = client.post(f"/exam/{exam.id}/questions/1/insights")
            r2 = client.post(f"/exam/{exam.id}/questions/1/insights")

        assert r1.status_code == 200 and r2.status_code == 200
        # A 2ª chamada (sem force) deve vir do cache: só 1 requisição ao Gemini.
        assert mock_client.models.generate_content.call_count == 1
        assert r2.json()["insights"][0]["insight"] == "Insight do Gemini."

    def test_force_regenera(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        sub = submission_factory(q.id)
        _seed_cluster(db, q.id, sub.id, label=0)
        mock_client = _mock_gemini_client({0: "Insight do Gemini."})

        with patch("app.llm.feedback_generator.genai.Client", return_value=mock_client):
            client.post(f"/exam/{exam.id}/questions/1/insights")
            client.post(f"/exam/{exam.id}/questions/1/insights?force=true")

        assert mock_client.models.generate_content.call_count == 2

    def test_gemini_indisponivel_retorna_503(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        sub = submission_factory(q.id)
        _seed_cluster(db, q.id, sub.id)

        with patch(
            "app.llm.feedback_generator.genai.Client",
            side_effect=RuntimeError("API indisponível"),
        ):
            resp = client.post(f"/exam/{exam.id}/questions/1/insights")

        assert resp.status_code == 503
