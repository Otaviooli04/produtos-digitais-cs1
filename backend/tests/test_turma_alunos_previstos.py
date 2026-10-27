"""Tamanho da turma informado pelo professor, o denominador da aquisição no funil."""


def _criar(client, **extra):
    return client.post("/turmas", json={"nome": "CS1 A", "codigo": "CS1", **extra})


class TestCriar:
    def test_cria_com_o_tamanho_e_devolve(self, client):
        resp = _criar(client, alunos_previstos=60)
        assert resp.status_code == 200
        assert resp.json()["alunos_previstos"] == 60
        assert client.get("/turmas").json()[0]["alunos_previstos"] == 60
        assert client.get(f"/turmas/{resp.json()['id']}").json()["alunos_previstos"] == 60

    def test_sem_o_campo_fica_nulo(self, client):
        assert _criar(client).json()["alunos_previstos"] is None

    def test_zero_e_recusado(self, client):
        assert _criar(client, alunos_previstos=0).status_code == 422

    def test_acima_de_mil_e_recusado(self, client):
        assert _criar(client, alunos_previstos=1001).status_code == 422


class TestEditar:
    def test_put_sem_o_campo_mantem_o_valor(self, client):
        turma_id = _criar(client, alunos_previstos=60).json()["id"]
        resp = client.put(f"/turmas/{turma_id}", json={"nome": "CS1 B", "codigo": "CS1"})
        assert resp.status_code == 200
        assert resp.json()["nome"] == "CS1 B"
        assert resp.json()["alunos_previstos"] == 60

    def test_put_com_null_limpa(self, client):
        turma_id = _criar(client, alunos_previstos=60).json()["id"]
        resp = client.put(f"/turmas/{turma_id}",
                          json={"nome": "CS1", "codigo": "CS1", "alunos_previstos": None})
        assert resp.json()["alunos_previstos"] is None

    def test_put_com_valor_troca(self, client):
        turma_id = _criar(client, alunos_previstos=60).json()["id"]
        resp = client.put(f"/turmas/{turma_id}",
                          json={"nome": "CS1", "codigo": "CS1", "alunos_previstos": 45})
        assert resp.json()["alunos_previstos"] == 45

    def test_put_com_zero_e_recusado(self, client):
        turma_id = _criar(client).json()["id"]
        resp = client.put(f"/turmas/{turma_id}",
                          json={"nome": "CS1", "codigo": "CS1", "alunos_previstos": 0})
        assert resp.status_code == 422
