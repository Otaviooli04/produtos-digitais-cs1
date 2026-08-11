import numpy as np
from unittest.mock import MagicMock, patch

from app.models.orm import QuestionCluster, Submission


def _mock_umap(n_out):
    umap = MagicMock()
    umap.fit_transform.return_value = np.random.rand(n_out, 2)
    return umap


def _mock_hdbscan(labels):
    hdbscan = MagicMock()
    hdbscan.fit_predict.return_value = np.array(labels)
    return hdbscan


def _patch_ml(labels):
    n = len(labels)
    umap_patch = patch(
        "app.ml.cluster.UMAP",
        side_effect=[_mock_umap(n), _mock_umap(n)],
    )
    hdbscan_patch = patch(
        "app.ml.cluster.HDBSCAN",
        return_value=_mock_hdbscan(labels),
    )
    return umap_patch, hdbscan_patch


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

    def test_clustering_retorna_clusters_e_scatter(self, client, exam_factory, submission_factory):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        # Duas categorias distintas: no nível 1 cada categoria forma um grupo.
        submission_factory(q.id, code="int main(){return 0;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 1;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 2;}", error_category="Erro de Compilação")
        submission_factory(q.id, code="int main(){return 3;}", error_category="Erro de Compilação")

        umap_p, hdbscan_p = _patch_ml([0, 0, 1, 1])
        with umap_p, hdbscan_p:
            resp = client.post(f"/exam/{exam.id}/questions/1/cluster")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_submissions"] == 4
        assert len(data["clusters"]) == 2
        assert len(data["scatter"]) == 4

    def test_cluster_id_persistido_nas_submissoes(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        subs = [submission_factory(q.id, code=f"int main(){{return {i};}}") for i in range(3)]

        umap_p, hdbscan_p = _patch_ml([0, 0, 1])
        with umap_p, hdbscan_p:
            resp = client.post(f"/exam/{exam.id}/questions/1/cluster")

        assert resp.status_code == 200
        db.expire_all()
        for sub in subs:
            updated = db.get(Submission, sub.id)
            assert updated.cluster_id is not None
            assert updated.umap_x is not None
            assert updated.umap_y is not None

    def test_question_cluster_registros_criados(self, client, exam_factory, submission_factory, db):
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        submission_factory(q.id, code="int main(){return 0;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 1;}", error_category="Saída Incorreta")
        submission_factory(q.id, code="int main(){return 2;}", error_category="Erro de Compilação")

        umap_p, hdbscan_p = _patch_ml([0, 0, 1])
        with umap_p, hdbscan_p:
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
            umap_p, hdbscan_p = _patch_ml([0, 0, 1])
            with umap_p, hdbscan_p:
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

        umap_p, hdbscan_p = _patch_ml([0, 0, 1, 1])
        with umap_p, hdbscan_p:
            resp = client.post(f"/exam/{exam.id}/questions/1/cluster")

        assert resp.status_code == 200
        clusters = resp.json()["clusters"]
        assert len(clusters) == 1
        assert clusters[0]["dominant_error"] == "Saída Incorreta"
