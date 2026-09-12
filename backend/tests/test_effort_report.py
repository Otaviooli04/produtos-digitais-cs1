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


class TestTrajetoriaDeErros:
    """`top_erros` diz qual é o erro mais comum da turma. A trajetória diz outra
    coisa: se ele está caindo ou voltando de uma prova para a outra."""

    def _prova_com_erros(self, db, professor, turma, titulo, categorias):
        from app.models.orm import Exam, Question, Submission
        from datetime import datetime, timedelta

        exam = Exam(filename=f"{titulo}.pdf", titulo=titulo, turma_id=turma.id,
                    created_at=datetime.utcnow() + timedelta(days=len(turma.exams)))
        db.add(exam)
        db.flush()
        questao = Question(exam_id=exam.id, number="1", statement="enunciado")
        db.add(questao)
        db.flush()
        for i, cat in enumerate(categorias):
            db.add(Submission(
                question_id=questao.id, code="int main(){}", error_category=cat,
                all_tests_passed=(cat == "Correto"), matricula=f"20260{i:02d}",
                submitted_at=datetime.utcnow(),
            ))
        db.commit()
        return exam

    def test_categoria_de_uma_prova_so_nao_entra(self, db, professor):
        from app.models.orm import Turma
        from app.services.turma_service import get_turma_analytics

        turma = Turma(nome="T", codigo="T1", professor_id=professor.id)
        db.add(turma)
        db.commit()
        self._prova_com_erros(db, professor, turma, "Lista 1", ["Off-by-One", "Off-by-One"])

        dados = get_turma_analytics(turma.id, db)
        assert dados["trajetoria"] == []

    def test_erro_que_cai_entre_provas(self, db, professor):
        from app.models.orm import Turma
        from app.services.turma_service import get_turma_analytics

        turma = Turma(nome="T", codigo="T2", professor_id=professor.id)
        db.add(turma)
        db.commit()
        self._prova_com_erros(db, professor, turma, "Lista 1", ["Off-by-One"] * 8 + ["Tudo no Main"] * 2)
        db.refresh(turma)
        self._prova_com_erros(db, professor, turma, "Prova 1", ["Off-by-One"] * 2 + ["Tudo no Main"] * 8)

        dados = get_turma_analytics(turma.id, db)
        por_cat = {t["error_category"]: t for t in dados["trajetoria"]}

        assert por_cat["Off-by-One"]["tendencia"] == "caindo"
        assert por_cat["Tudo no Main"]["tendencia"] == "subindo"
        assert [p["titulo"] for p in por_cat["Off-by-One"]["pontos"]] == ["Lista 1", "Prova 1"]

    def test_proporcao_ignora_tamanho_da_prova(self, db, professor):
        """Prova com mais envios teria mais ocorrências de tudo. Sem proporção,
        a dificuldade pareceria crescer só porque a turma enviou mais."""
        from app.models.orm import Turma
        from app.services.turma_service import get_turma_analytics

        turma = Turma(nome="T", codigo="T3", professor_id=professor.id)
        db.add(turma)
        db.commit()
        self._prova_com_erros(db, professor, turma, "Lista 1", ["Off-by-One"] * 5 + ["Tudo no Main"] * 5)
        db.refresh(turma)
        self._prova_com_erros(db, professor, turma, "Prova 1",
                              ["Off-by-One"] * 10 + ["Tudo no Main"] * 10)

        dados = get_turma_analytics(turma.id, db)
        por_cat = {t["error_category"]: t for t in dados["trajetoria"]}
        assert por_cat["Off-by-One"]["tendencia"] == "estavel"
        assert por_cat["Off-by-One"]["pontos"][1]["ocorrencias"] == 10

    def test_cada_prova_traz_os_proprios_erros(self, db, professor):
        from app.models.orm import Turma
        from app.services.turma_service import get_turma_analytics

        turma = Turma(nome="T", codigo="T4", professor_id=professor.id)
        db.add(turma)
        db.commit()
        self._prova_com_erros(db, professor, turma, "Lista 1", ["Off-by-One", "Correto"])

        dados = get_turma_analytics(turma.id, db)
        (prova,) = dados["provas"]
        assert prova["titulo"] == "Lista 1"
        assert prova["top_erros"] == [{"error_category": "Off-by-One", "count": 1}]
