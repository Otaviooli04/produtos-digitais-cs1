from app.models.orm import QuestionCluster, Submission


class TestClustering:
    def test_submissoes_insuficientes_retorna_422(self, client, exam_factory, submission_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        submission_factory(q.id)
        submission_factory(q.id)

        resp = client.post(f"/exam/{exam.id}/questions/1/cluster")
        assert resp.status_code == 422

    def test_questao_inexistente_retorna_404(self, client, exam_factory):
        exam = exam_factory()
        resp = client.post(f"/exam/{exam.id}/questions/99/cluster")
        assert resp.status_code == 404

    def test_clustering_retorna_os_grupos(self, client, exam_factory, submission_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        # Duas categorias distintas: no nível 1 cada categoria forma um grupo.
        submission_factory(q.id, code="int main(){return 0;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 1;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 2;}", error_category="Erro de Compilação")
        submission_factory(q.id, code="int main(){return 3;}", error_category="Erro de Compilação")

        resp = client.post(f"/exam/{exam.id}/questions/1/cluster")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_submissions"] == 4
        assert len(data["clusters"]) == 2

    def test_cluster_id_persistido_nas_submissoes(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        subs = [submission_factory(q.id, code=f"int main(){{return {i};}}") for i in range(3)]

        resp = client.post(f"/exam/{exam.id}/questions/1/cluster")

        assert resp.status_code == 200
        db.expire_all()
        for sub in subs:
            updated = db.get(Submission, sub.id)
            assert updated.cluster_id is not None

    def test_question_cluster_registros_criados(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        submission_factory(q.id, code="int main(){return 0;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 1;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 2;}", error_category="Erro de Compilação")

        client.post(f"/exam/{exam.id}/questions/1/cluster")

        clusters = db.query(QuestionCluster).filter(QuestionCluster.question_id == q.id).all()
        assert len(clusters) == 2
        assert sorted(c.size for c in clusters) == [1, 2]
        assert {c.dominant_error for c in clusters} == {"Saída Incorreta", "Erro de Compilação"}

    def test_clustering_idempotente_sobrescreve_anterior(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        submission_factory(q.id, code="int main(){return 0;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 1;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 2;}", error_category="Erro de Compilação")

        for _ in range(2):
            resp = client.post(f"/exam/{exam.id}/questions/1/cluster")
            assert resp.status_code == 200

        clusters = db.query(QuestionCluster).filter(QuestionCluster.question_id == q.id).all()
        assert len(clusters) == 2

    def test_categoria_pequena_vira_um_grupo(self, client, exam_factory, submission_factory):
        # No agrupamento em dois níveis, uma categoria abaixo do mínimo de
        # sub-agrupamento forma um grupo único, sem super-segmentar.
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        for i in range(4):
            submission_factory(q.id, code=f"int main(){{return {i};}}", error_category="Saída Incorreta")

        resp = client.post(f"/exam/{exam.id}/questions/1/cluster")

        assert resp.status_code == 200
        clusters = resp.json()["clusters"]
        assert len(clusters) == 1
        assert clusters[0]["dominant_error"] == "Saída Incorreta"


class TestListaDeAlunosDoGrupo:
    """A lista de quem caiu em cada grupo saía das coordenadas do gráfico. Quem
    não tinha coordenada ficava no grupo certo e invisível para o professor, e
    era o caso de toda submissão agrupada fora de uma passada completa."""

    def test_todo_agrupado_aparece_na_lista(self, client, exam_factory, submission_factory, db):
        from app.ml.cluster import cluster_question

        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        for i in range(3):
            sub = submission_factory(q.id, code=f"int main(){{return {i};}}",
                                     error_category="Saída Incorreta")
            sub.matricula = f"202600{i}"
        db.commit()
        cluster_question(q.id, db)

        data = client.get(f"/exam/{exam.id}/questions/1/groups").json()
        (grupo,) = data["clusters"]
        assert grupo["alunos"] == ["2026000", "2026001", "2026002"]
        assert grupo["size"] == len(grupo["alunos"])

    def test_aluno_sem_matricula_aparece_pelo_nome(
        self, client, exam_factory, submission_factory, db
    ):
        from app.auth.service import hash_password
        from app.ml.cluster import cluster_question
        from app.models.orm import Student

        aluno = Student(email="semmat@aluno.com", nome="Lucas Moreira",
                        senha_hash=hash_password("senha12345"))
        db.add(aluno)
        db.flush()

        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        for i in range(2):
            sub = submission_factory(q.id, code=f"int main(){{return {i};}}",
                                     error_category="Saída Incorreta")
            sub.matricula = f"202600{i}"
        sem_matricula = submission_factory(q.id, code="int main(){return 9;}",
                                           error_category="Saída Incorreta")
        sem_matricula.student_id = aluno.id
        sem_matricula.matricula = None
        db.commit()
        cluster_question(q.id, db)

        data = client.get(f"/exam/{exam.id}/questions/1/groups").json()
        (grupo,) = data["clusters"]
        assert "Lucas Moreira" in grupo["alunos"]
        # Matrículas primeiro, quem entrou sem ela depois.
        assert grupo["alunos"][-1] == "Lucas Moreira"
