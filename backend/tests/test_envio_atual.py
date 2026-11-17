"""O estado atual de cada aluno é o último envio dele: quem errou e depois
acertou conta como acerto nos resultados, no desempenho e nos grupos."""
from types import SimpleNamespace

from app.core.envio_atual import chave_do_aluno, atuais_por_aluno
from app.services.turma_service import get_turma_analytics


def _envio(id, student_id=None, matricula=None, categoria="Saída Incorreta"):
    return SimpleNamespace(id=id, student_id=student_id, matricula=matricula,
                           error_category=categoria)


class TestAtuaisPorAluno:
    def test_fica_o_ultimo_de_cada_aluno_na_ordem_de_chegada(self):
        envios = [_envio(3, student_id=1), _envio(1, student_id=1), _envio(2, matricula="A05"),
                  _envio(5, matricula="A05"), _envio(4)]
        assert [e.id for e in atuais_por_aluno(envios)] == [3, 4, 5]

    def test_quem_ja_acertou_fica_no_ultimo_acerto(self):
        envios = [_envio(1, student_id=1), _envio(2, student_id=1, categoria="Correto"),
                  _envio(3, student_id=1), _envio(4, student_id=2, categoria="Correto"),
                  _envio(5, student_id=2, categoria="Correto")]
        assert [e.id for e in atuais_por_aluno(envios)] == [2, 5]

    def test_conta_vale_mais_que_a_matricula(self):
        assert chave_do_aluno(_envio(1, student_id=7, matricula="2026")) == ("conta", 7)
        assert chave_do_aluno(_envio(1, matricula="2026")) == ("rotulo", "2026")
        assert chave_do_aluno(_envio(9)) == ("envio", 9)


def _turma_com_quem_corrigiu(exam_factory, submission_factory, db):
    """Questão 1: 2026001 erra e depois acerta, 2026002 só erra, 2026003 só acerta."""
    exam = exam_factory(questions=[{"number": "1"}])
    q = exam.questions[0]
    envios = [("2026001", "Saída Incorreta", False), ("2026002", "Saída Incorreta", False),
              ("2026001", "Correto", True), ("2026003", "Correto", True)]
    for i, (matricula, categoria, passou) in enumerate(envios):
        sub = submission_factory(q.id, code=f"int main(){{return {i};}}",
                                 error_category=categoria, all_tests_passed=passou)
        sub.matricula = matricula
    db.commit()
    return exam, q


class TestResultados:
    def test_contam_o_ultimo_envio_de_cada_aluno(
        self, client, exam_factory, submission_factory, db
    ):
        exam, _ = _turma_com_quem_corrigiu(exam_factory, submission_factory, db)
        (questao,) = client.get(f"/exam/{exam.id}/results").json()["questions"]
        assert questao["total_submissions"] == 4
        assert questao["total_alunos"] == 3
        assert questao["passed_count"] == 2
        assert questao["error_distribution"] == [
            {"error_category": "Saída Incorreta", "count": 1, "matriculas": ["2026002"]}]
        assert [s["matricula"] for s in questao["submissions"]] == ["2026001", "2026002", "2026003"]


class TestRespostas:
    def test_marca_o_envio_atual_de_cada_aluno(
        self, client, exam_factory, submission_factory, db
    ):
        exam, _ = _turma_com_quem_corrigiu(exam_factory, submission_factory, db)
        envios = client.get(f"/exam/{exam.id}/questions/1/submissions").json()["submissions"]
        assert len(envios) == 4
        atuais = {(e["matricula"], e["error_category"]) for e in envios if e["atual"]}
        assert atuais == {("2026001", "Correto"), ("2026002", "Saída Incorreta"),
                          ("2026003", "Correto")}


class TestDesempenho:
    def test_erros_sao_os_que_ainda_estao_em_aberto(
        self, exam_factory, submission_factory, db, professor
    ):
        exam, _ = _turma_com_quem_corrigiu(exam_factory, submission_factory, db)
        dados = get_turma_analytics(exam.turma_id, db, professor_id=professor.id)
        assert dados["top_erros"] == [{"error_category": "Saída Incorreta", "count": 1}]
        (prova,) = dados["provas"]
        assert prova["top_erros"] == [{"error_category": "Saída Incorreta", "count": 1}]
        assert prova["total_submissoes"] == 4
        assert dados["total_submissoes"] == 4


class TestGruposAcompanhamOsEnvios:
    def _tres_alunos_errando(self, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        envios = []
        for i, matricula in enumerate(["2026001", "2026002", "2026003"]):
            sub = submission_factory(q.id, code=f"int main(){{return {i};}}",
                                     error_category="Saída Incorreta", all_tests_passed=False)
            sub.matricula = matricula
            envios.append(sub)
        db.commit()
        return exam, q, envios

    def test_excluir_o_envio_que_corrigiu_devolve_o_aluno_ao_erro(
        self, client, exam_factory, submission_factory, db
    ):
        from app.ml.cluster import cluster_question
        from app.services.submission_service import delete_submission

        exam, q, _ = self._tres_alunos_errando(exam_factory, submission_factory, db)
        corrigiu = submission_factory(q.id, code="int main(){return 9;}")
        corrigiu.matricula = "2026001"
        db.commit()
        cluster_question(q.id, db)
        grupos = {g["dominant_error"]: g for g in
                  client.get(f"/exam/{exam.id}/questions/1/groups").json()["clusters"]}
        assert grupos["Correto"]["alunos"] == ["2026001"]

        delete_submission(corrigiu, db)
        grupos = {g["dominant_error"]: g for g in
                  client.get(f"/exam/{exam.id}/questions/1/groups").json()["clusters"]}
        assert "Correto" not in grupos
        assert grupos["Saída Incorreta"]["alunos"] == ["2026001", "2026002", "2026003"]

    def test_abaixo_de_tres_alunos_os_grupos_antigos_saem(
        self, client, exam_factory, submission_factory, db
    ):
        from app.ml.cluster import cluster_question
        from app.services.submission_service import delete_submission

        exam, q, envios = self._tres_alunos_errando(exam_factory, submission_factory, db)
        cluster_question(q.id, db)
        assert client.get(f"/exam/{exam.id}/questions/1/groups").json()["has_groups"] is True

        delete_submission(envios[0], db)
        assert client.get(f"/exam/{exam.id}/questions/1/groups").json()["has_groups"] is False
        db.refresh(envios[1])
        assert envios[1].cluster_id is None

    def test_resposta_do_professor_volta_quando_o_erro_reaparece(
        self, client, exam_factory, submission_factory, db
    ):
        from app.ml.cluster import cluster_question
        from app.models.orm import QuestionCluster

        exam, q, envios = self._tres_alunos_errando(exam_factory, submission_factory, db)
        cluster_question(q.id, db)
        grupo = db.query(QuestionCluster).filter_by(question_id=q.id).one()
        grupo.resposta_professor = "Divida pela quantidade."
        chave = grupo.chave
        db.commit()

        for i, matricula in enumerate(["2026001", "2026002", "2026003"]):
            sub = submission_factory(q.id, code=f"int main(){{return {i + 10};}}")
            sub.matricula = matricula
        db.commit()
        cluster_question(q.id, db)
        adormecido = db.query(QuestionCluster).filter_by(question_id=q.id, chave=chave).one()
        assert adormecido.cluster_label is None and adormecido.size == 0
        assert adormecido.resposta_professor == "Divida pela quantidade."
        grupos = client.get(f"/exam/{exam.id}/questions/1/groups").json()["clusters"]
        assert [g["dominant_error"] for g in grupos] == ["Correto"]

        novo = submission_factory(q.id, code="int main(){return 50;}",
                                  error_category="Saída Incorreta", all_tests_passed=False)
        novo.matricula = "2026004"
        db.commit()
        cluster_question(q.id, db)
        db.refresh(adormecido)
        assert adormecido.cluster_label is not None and adormecido.size == 1
        insights = client.get(f"/exam/{exam.id}/questions/1/groups").json()["insights"]
        assert "Divida pela quantidade." in [i["resposta_professor"] for i in insights]


class TestCorretoPrevalece:
    def test_resultados_contam_quem_acertou_e_depois_errou_como_correto(
        self, client, exam_factory, submission_factory, db
    ):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        envios = [("2026001", "Correto", True), ("2026001", "Saída Incorreta", False),
                  ("2026002", "Saída Incorreta", False)]
        for i, (matricula, categoria, passou) in enumerate(envios):
            sub = submission_factory(q.id, code=f"int main(){{return {i};}}",
                                     error_category=categoria, all_tests_passed=passou)
            sub.matricula = matricula
        db.commit()
        (questao,) = client.get(f"/exam/{exam.id}/results").json()["questions"]
        assert (questao["total_alunos"], questao["passed_count"]) == (2, 1)
        assert questao["error_distribution"][0]["matriculas"] == ["2026002"]
