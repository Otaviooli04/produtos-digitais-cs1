"""Relatório de esforço economizado: quantas submissões chegaram e em quantos
itens de mesmo sintoma elas colapsam para o professor."""
from app.models.orm import SubmissionTestResult


def _com_testes(db, sub, resultados):
    """Anexa resultados de teste à submissão (define a assinatura de falha)."""
    for passou in resultados:
        db.add(SubmissionTestResult(
            submission_id=sub.id, input="1", expected_output="x",
            actual_output="x" if passou else "y", passed=passou,
        ))
    db.commit()
    db.refresh(sub)
    return sub


class TestEffortReport:
    def test_submissoes_de_mesmo_sintoma_viram_um_item(self, client, db, exam_factory, submission_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        for _ in range(3):
            _com_testes(db, submission_factory(
                q.id, error_category="Saída Incorreta", all_tests_passed=False), [True, False])
        _com_testes(db, submission_factory(
            q.id, error_category="Saída Incorreta", all_tests_passed=False), [False, False])

        data = client.get(f"/exam/{exam.id}/effort-report").json()
        assert data["total_submissoes"] == 4
        assert data["itens_a_revisar"] == 2
        assert data["fator_reducao"] == 2.0
        assert data["minutos_economizados"] == 2 * data["minutos_por_item"]
        assert data["questoes"][0]["question_number"] == "1"

    def test_categorias_diferentes_nao_se_misturam(self, client, db, exam_factory, submission_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        submission_factory(q.id, error_category="Saída Incorreta", all_tests_passed=False)
        erro_compilacao = submission_factory(
            q.id, error_category="Erro de Compilação", all_tests_passed=False)
        erro_compilacao.compile_error = "erro"
        db.commit()

        data = client.get(f"/exam/{exam.id}/effort-report").json()
        assert data["itens_a_revisar"] == 2
        assert data["fator_reducao"] == 1.0

    def test_prova_sem_submissao(self, client, exam_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        data = client.get(f"/exam/{exam.id}/effort-report").json()
        assert data["total_submissoes"] == 0
        assert data["fator_reducao"] is None
        assert data["minutos_economizados"] == 0

    def test_prova_de_outro_professor(self, client, db, exam_factory):
        from app.models.orm import Professor, Turma

        outro = Professor(email="outro@prof.com", nome="Outro", senha_hash="x")
        db.add(outro)
        db.flush()
        exam = exam_factory(questions=[{"number": "1"}])
        db.get(Turma, exam.turma_id).professor_id = outro.id
        db.commit()

        assert client.get(f"/exam/{exam.id}/effort-report").status_code == 404
