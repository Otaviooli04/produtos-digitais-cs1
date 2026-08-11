import json
from unittest.mock import patch

from tests.conftest import gemini_response


GEMINI_STRUCTURE = json.dumps({
    "questions": [
        {
            "number": "1",
            "type": "code",
            "statement": "Escreva um programa que leia um número e diga se é par ou ímpar.",
            "required_structures": ["If"],
            "forbidden_structures": [],
            "requires_loop": False,
        }
    ]
})

FAKE_PDF_BYTES = b"%PDF-1.4 fake"


def _mock_upload_dependencies():
    parse = patch("app.services.exam_service.parse_document", return_value="texto extraído")
    gemini = patch(
        "app.engine.semantic_extractor.genai.Client",
        return_value=_mock_gemini_client(GEMINI_STRUCTURE),
    )
    return parse, gemini


def _mock_gemini_client(response_text: str):
    from unittest.mock import MagicMock
    client = MagicMock()
    client.models.generate_content.return_value = gemini_response(response_text)
    return client


class TestExamUpload:
    def test_upload_cria_prova_e_questoes(self, client, run_jobs_sync):
        parse, gemini = _mock_upload_dependencies()
        with parse, gemini:
            resp = client.post(
                "/exam/upload",
                files={"file": ("prova.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )
        # O upload é assíncrono: a rota cria a prova e dispara a extração em job.
        assert resp.status_code == 200
        data = resp.json()
        exam_id = data["exam_id"]
        assert data["job_id"]

        # run_jobs_sync já rodou o job; a prova deve ter as questões extraídas.
        exam = client.get(f"/exam/{exam_id}").json()
        assert exam["filename"] == "prova.pdf"
        assert len(exam["questions"]) == 1
        assert exam["questions"][0]["number"] == "1"
        assert exam["questions"][0]["required_structures"] == ["If"]

    def test_upload_formato_invalido_retorna_400(self, client):
        resp = client.post(
            "/exam/upload",
            files={"file": ("prova.txt", b"conteudo", "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_gemini_falha_marca_job_com_erro(self, client, run_jobs_sync):
        parse = patch("app.services.exam_service.parse_document", return_value="texto")
        gemini = patch(
            "app.engine.semantic_extractor.genai.Client",
            side_effect=RuntimeError("API indisponível"),
        )
        with parse, gemini:
            resp = client.post(
                "/exam/upload",
                files={"file": ("prova.pdf", FAKE_PDF_BYTES, "application/pdf")},
            )
        # A falha do Gemini ocorre em segundo plano: a rota responde 200 e o erro
        # fica registrado no status do job, sem questões na prova.
        assert resp.status_code == 200
        data = resp.json()
        job = client.get(f"/jobs/{data['job_id']}").json()
        assert job["status"] == "error"

        exam = client.get(f"/exam/{data['exam_id']}").json()
        assert exam["questions"] == []


class TestGetExam:
    def test_get_exam_retorna_questoes(self, client, exam_factory):
        exam = exam_factory(questions=[{"number": "1", "statement": "Enunciado"}])
        resp = client.get(f"/exam/{exam.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == exam.id
        assert len(resp.json()["questions"]) == 1

    def test_get_exam_inexistente_retorna_404(self, client):
        resp = client.get("/exam/99999")
        assert resp.status_code == 404


class TestTestCases:
    def test_add_testcases_retorna_contagem(self, client, exam_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        resp = client.post(
            f"/exam/{exam.id}/questions/1/testcases",
            json={"test_cases": [
                {"input": "2", "expected_output": "par"},
                {"input": "3", "expected_output": "impar"},
            ]},
        )
        assert resp.status_code == 200
        assert resp.json()["added"] == 2

    def test_add_testcases_questao_inexistente_retorna_404(self, client, exam_factory):
        exam = exam_factory()
        resp = client.post(
            f"/exam/{exam.id}/questions/99/testcases",
            json={"test_cases": [{"input": "1", "expected_output": "1"}]},
        )
        assert resp.status_code == 404


class TestExamResults:
    def test_results_sem_submissoes(self, client, exam_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        resp = client.get(f"/exam/{exam.id}/results")
        assert resp.status_code == 200
        data = resp.json()
        assert data["exam_id"] == exam.id
        assert data["questions"][0]["total_submissions"] == 0
        assert data["questions"][0]["passed_count"] == 0

    def test_results_agrega_submissoes_corretamente(self, client, exam_factory, submission_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        submission_factory(q.id, error_category="Correto", all_tests_passed=True)
        submission_factory(q.id, error_category="Saída Incorreta", all_tests_passed=False)

        resp = client.get(f"/exam/{exam.id}/results")
        assert resp.status_code == 200
        result = resp.json()["questions"][0]
        assert result["total_submissions"] == 2
        assert result["passed_count"] == 1
        # "Correto" não é erro: a distribuição lista só as categorias de erro
        assert len(result["error_distribution"]) == 1
        assert result["error_distribution"][0]["error_category"] == "Saída Incorreta"

    def test_results_prova_inexistente_retorna_404(self, client):
        resp = client.get("/exam/99999/results")
        assert resp.status_code == 404
