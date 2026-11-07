"""Lista de aquecimento (RF05, experimento 3): a questão curta que o professor
adiciona à turma para o primeiro envio acontecer no primeiro acesso."""
import pytest
from fastapi.testclient import TestClient

from app.auth.service import create_access_token
from app.auth.student_service import create_student_token
from app.main import app
from app.models.database import get_db
from app.models.orm import Enrollment, Exam, Professor, Student, Turma
from app.services.exam_service import impedimentos_para_publicar


def _turma(client):
    return client.post("/turmas", json={"nome": "CS1 A", "codigo": "CS1"}).json()["id"]


def _adicionar(client, turma_id):
    return client.post(f"/turmas/{turma_id}/lista-de-aquecimento")


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestAdicionar:
    def test_nasce_como_lista_em_rascunho_com_a_questao_e_os_casos(self, client, db):
        turma_id = _turma(client)
        resp = _adicionar(client, turma_id)
        assert resp.status_code == 200

        exam = db.get(Exam, resp.json()["exam_id"])
        assert exam.turma_id == turma_id
        assert exam.titulo == "Lista de aquecimento"
        assert exam.modo == Exam.MODO_TREINO
        assert exam.publicada is False
        assert exam.abre_em is None and exam.fecha_em is None and exam.max_tentativas is None

        assert [q.number for q in exam.questions] == ["1"]
        questao = exam.questions[0]
        assert questao.statement == "Leia duas notas e imprima a média com uma casa decimal."
        assert sorted((t.input, t.expected_output) for t in questao.test_cases) == [
            ("10 5", "7.5"), ("6 6", "6.0"), ("8 7", "7.5")]

    def test_pode_ser_publicada_sem_mexer_em_nada(self, client, db):
        exam_id = _adicionar(client, _turma(client)).json()["exam_id"]
        assert impedimentos_para_publicar(db.get(Exam, exam_id)) == []
        assert client.patch(f"/exam/{exam_id}", json={"publicada": True}).status_code == 200
        db.expire_all()
        assert db.get(Exam, exam_id).publicada is True

    def test_resultados_trazem_o_titulo(self, client):
        exam_id = _adicionar(client, _turma(client)).json()["exam_id"]
        assert client.get(f"/exam/{exam_id}/results").json()["titulo"] == "Lista de aquecimento"

    def test_repetir_nao_duplica(self, client, db):
        turma_id = _turma(client)
        primeira = _adicionar(client, turma_id).json()["exam_id"]
        assert _adicionar(client, turma_id).json()["exam_id"] == primeira
        assert db.query(Exam).filter_by(turma_id=turma_id).count() == 1

    def test_cada_turma_tem_a_sua(self, client):
        primeira = _adicionar(client, _turma(client)).json()["exam_id"]
        assert _adicionar(client, _turma(client)).json()["exam_id"] != primeira

    def test_outra_atividade_da_turma_nao_conta(self, client, db):
        turma_id = _turma(client)
        db.add(Exam(filename="prova.pdf", raw_text="", turma_id=turma_id, titulo="Lista de aquecimento"))
        db.commit()
        exam_id = _adicionar(client, turma_id).json()["exam_id"]
        assert db.get(Exam, exam_id).filename == "lista-de-aquecimento"


class TestPosse:
    def test_turma_de_outro_professor_da_404(self, client, db):
        outro = Professor(email="outro@teste.com", nome="Outro", senha_hash="x")
        db.add(outro)
        db.flush()
        turma = Turma(nome="Outra", codigo="O", professor_id=outro.id)
        db.add(turma)
        db.commit()
        assert _adicionar(client, turma.id).status_code == 404
        assert db.query(Exam).filter_by(turma_id=turma.id).count() == 0


class TestPapel:
    @pytest.fixture()
    def cliente_sem_atalho(self, db):
        """O `client` da suíte já entra como professor, então aqui o token vale de verdade."""
        app.dependency_overrides[get_db] = lambda: db
        yield TestClient(app)
        app.dependency_overrides.clear()

    def test_sem_token_da_401(self, cliente_sem_atalho):
        assert cliente_sem_atalho.post("/turmas/1/lista-de-aquecimento").status_code == 401

    def test_token_de_aluno_da_401(self, cliente_sem_atalho, db):
        aluno = Student(email="ana@teste.com", nome="Ana", senha_hash="x")
        db.add(aluno)
        db.commit()
        resp = cliente_sem_atalho.post("/turmas/1/lista-de-aquecimento",
                                       headers=_auth(create_student_token(aluno.id)))
        assert resp.status_code == 401

    def test_professor_dono_entra_pelo_token(self, cliente_sem_atalho, db):
        dono = Professor(email="dono@teste.com", nome="Dono", senha_hash="x")
        db.add(dono)
        db.flush()
        turma = Turma(nome="Minha", codigo="M", professor_id=dono.id)
        db.add(turma)
        db.commit()
        resp = cliente_sem_atalho.post(f"/turmas/{turma.id}/lista-de-aquecimento",
                                       headers=_auth(create_access_token(dono.id)))
        assert resp.status_code == 200


class TestAluno:
    def test_rascunho_nao_aparece_e_publicada_aparece(self, client, db):
        turma_id = _turma(client)
        exam_id = _adicionar(client, turma_id).json()["exam_id"]
        aluno = Student(email="ana@teste.com", nome="Ana", senha_hash="x")
        db.add(aluno)
        db.flush()
        db.add(Enrollment(student_id=aluno.id, turma_id=turma_id))
        db.commit()
        cabecalho = _auth(create_student_token(aluno.id))

        assert client.get("/aluno/atividades", headers=cabecalho).json() == []
        client.patch(f"/exam/{exam_id}", json={"publicada": True})
        atividades = client.get("/aluno/atividades", headers=cabecalho).json()
        assert [a["exam_id"] for a in atividades] == [exam_id]
