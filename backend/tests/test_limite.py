import pytest
from fastapi.testclient import TestClient

from app.auth.service import hash_password
from app.auth.student_service import create_student_token
from app.core.limite import (
    CADASTRO, ENTRAR_NA_TURMA, ENVIO_DO_ALUNO, LOGIN_POR_EMAIL, LOGIN_POR_IP, Limitador, Regra,
    limitador, mensagem_de_espera,
)
from app.api.routes import exam, student_activity, submission, treino
from app.main import app
from app.models.database import get_db
from app.models.orm import Student


class Relogio:
    def __init__(self):
        self.agora = 1000.0

    def __call__(self):
        return self.agora


REGRA = Regra("teste", maximo=3, janela=60)


def test_deixa_passar_ate_o_maximo_e_bloqueia_o_seguinte():
    lim = Limitador(relogio=Relogio())
    assert [lim.espera("a", REGRA) for _ in range(3)] == [0, 0, 0]
    assert lim.espera("a", REGRA) == 60


def test_libera_quando_a_janela_anda():
    relogio = Relogio()
    lim = Limitador(relogio=relogio)
    for _ in range(3):
        lim.espera("a", REGRA)
    relogio.agora += 20
    assert lim.espera("a", REGRA) == 40
    relogio.agora += 40
    assert lim.espera("a", REGRA) == 0


def test_pedido_bloqueado_nao_conta():
    relogio = Relogio()
    lim = Limitador(relogio=relogio)
    for _ in range(3):
        lim.espera("a", REGRA)
    for _ in range(5):
        lim.espera("a", REGRA)
    relogio.agora += 60
    assert lim.espera("a", REGRA) == 0


def test_cada_chave_e_cada_regra_contam_em_separado():
    lim = Limitador(relogio=Relogio())
    for _ in range(3):
        lim.espera("a", REGRA)
    assert lim.espera("b", REGRA) == 0
    assert lim.espera("a", Regra("outra", maximo=3, janela=60)) == 0


def test_varredura_tira_as_chaves_vencidas():
    relogio = Relogio()
    lim = Limitador(relogio=relogio, varrer_acima_de=2)
    lim.espera("a", REGRA)
    lim.espera("b", REGRA)
    relogio.agora += 61
    lim.espera("c", REGRA)
    assert lim.chaves() == 1


def test_mensagem_em_segundos_e_em_minutos():
    assert mensagem_de_espera(1) == "Muitas tentativas seguidas. Espere 1 segundo e tente de novo."
    assert mensagem_de_espera(42) == "Muitas tentativas seguidas. Espere 42 segundos e tente de novo."
    assert mensagem_de_espera(61) == "Muitas tentativas seguidas. Espere 2 minutos e tente de novo."


def test_regras_aprovadas_no_desenho():
    assert (LOGIN_POR_IP.maximo, LOGIN_POR_IP.janela) == (60, 60)
    assert (LOGIN_POR_EMAIL.maximo, LOGIN_POR_EMAIL.janela) == (10, 60)
    assert (CADASTRO.maximo, CADASTRO.janela) == (100, 3600)
    assert (ENTRAR_NA_TURMA.maximo, ENTRAR_NA_TURMA.janela) == (10, 60)
    assert (ENVIO_DO_ALUNO.maximo, ENVIO_DO_ALUNO.janela) == (10, 60)


# --- nas rotas ---

@pytest.fixture()
def cliente(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _aluno(db, email):
    s = Student(email=email, nome="Aluno", matricula=email[:6], senha_hash=hash_password("senha1234"))
    db.add(s)
    db.commit()
    return s


def test_login_do_aluno_bloqueia_o_pedido_11_com_retry_after(db, cliente):
    _aluno(db, "limite@teste.local")
    corpo = {"email": "limite@teste.local", "senha": "errada123"}
    codigos = [cliente.post("/aluno/login", json=corpo).status_code for _ in range(10)]
    assert codigos == [401] * 10
    r = cliente.post("/aluno/login", json=corpo)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0
    assert r.json()["detail"].startswith("Muitas tentativas seguidas.")


def test_login_de_outro_email_no_mesmo_ip_segue_liberado(db, cliente):
    for _ in range(10):
        cliente.post("/aluno/login", json={"email": "um@teste.local", "senha": "errada123"})
    r = cliente.post("/aluno/login", json={"email": "dois@teste.local", "senha": "errada123"})
    assert r.status_code == 401


def test_login_do_professor_tambem_tem_limite(db, cliente):
    corpo = {"email": "prof@teste.local", "nome": "Prof", "senha": "errada123"}
    for _ in range(10):
        cliente.post("/auth/login", json=corpo)
    assert cliente.post("/auth/login", json=corpo).status_code == 429


def test_cadastro_do_aluno_bloqueia_depois_do_maximo_por_ip(db, cliente):
    # Enche o contador direto: cem cadastros com bcrypt deixariam a suíte lenta.
    for _ in range(CADASTRO.maximo - 1):
        assert limitador.espera("testclient", CADASTRO) == 0
    r = cliente.post("/aluno/register", json={
        "email": "cad-ultimo@teste.local", "nome": "Aluno", "matricula": "m1", "senha": "senha1234"})
    assert r.status_code == 201
    r = cliente.post("/aluno/register", json={
        "email": "cad-bloqueado@teste.local", "nome": "Aluno", "matricula": "m2", "senha": "senha1234"})
    assert r.status_code == 429


def test_envio_do_aluno_conta_por_aluno_e_nao_por_ip(db, cliente):
    ana = _aluno(db, "ana@teste.local")
    bia = _aluno(db, "bia@teste.local")
    url = "/aluno/atividades/999999/questoes/1/submissoes"
    corpo = {"code": "int main(){return 0;}"}
    cab_ana = {"Authorization": f"Bearer {create_student_token(ana.id)}"}
    cab_bia = {"Authorization": f"Bearer {create_student_token(bia.id)}"}
    for _ in range(10):
        assert cliente.post(url, json=corpo, headers=cab_ana).status_code == 404
    assert cliente.post(url, json=corpo, headers=cab_ana).status_code == 429
    assert cliente.post(url, json=corpo, headers=cab_bia).status_code == 404


def test_entrar_na_turma_bloqueia_chute_de_codigo_por_aluno(db, cliente):
    ana = _aluno(db, "chute-ana@teste.local")
    bia = _aluno(db, "chute-bia@teste.local")
    corpo = {"codigo_acesso": "ZZZZZZ"}
    cab_ana = {"Authorization": f"Bearer {create_student_token(ana.id)}"}
    cab_bia = {"Authorization": f"Bearer {create_student_token(bia.id)}"}
    for _ in range(10):
        assert cliente.post("/aluno/turmas/entrar", json=corpo, headers=cab_ana).status_code == 404
    r = cliente.post("/aluno/turmas/entrar", json=corpo, headers=cab_ana)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0
    assert cliente.post("/aluno/turmas/entrar", json=corpo, headers=cab_bia).status_code == 404


def test_pedido_sem_token_recebe_401_e_nao_gasta_o_limite(db, cliente):
    url = "/aluno/atividades/999999/questoes/1/submissoes"
    for _ in range(12):
        assert cliente.post(url, json={"code": "x"}).status_code in (401, 403)


def test_rotas_que_disparam_docker_ou_gemini_tem_limite():
    protegidas = {
        ("POST", "/aluno/atividades/{exam_id}/questoes/{question_number}/submissoes"),
        ("POST", "/aluno/tentativas/{submission_id}/ajuda"),
        ("POST", "/aluno/treino/gerar"),
        ("POST", "/aluno/treino/{exercicio_id}/tentativas"),
        ("POST", "/submission/evaluate"),
        ("POST", "/submission/{submission_id}/reevaluate"),
        ("POST", "/exam/upload"),
        ("POST", "/exam/{exam_id}/submissions/bulk"),
        ("POST", "/exam/{exam_id}/questions/{question_number}/insights"),
    }
    com_limite = {
        (metodo, rota.path)
        for modulo in (exam, student_activity, submission, treino)
        for rota in modulo.router.routes
        if any(getattr(d.call, "regra_do_limite", None) for d in rota.dependant.dependencies)
        for metodo in rota.methods
    }
    assert protegidas <= com_limite


def test_varredura_roda_no_maximo_uma_vez_por_minuto(monkeypatch):
    relogio = Relogio()
    lim = Limitador(relogio=relogio, varrer_acima_de=1)
    chamadas = []
    original = lim._varrer
    monkeypatch.setattr(lim, "_varrer", lambda agora: (chamadas.append(agora), original(agora)))
    for chave in "abcde":
        lim.espera(chave, REGRA)
    assert len(chamadas) == 1
    relogio.agora += 60
    lim.espera("f", REGRA)
    assert len(chamadas) == 2


def test_teto_descarta_a_chave_mais_antiga():
    lim = Limitador(relogio=Relogio(), teto=3)
    for chave in ("a", "b", "c", "d"):
        lim.espera(chave, REGRA)
    assert lim.chaves() == 3
    for _ in range(3):
        lim.espera("a", REGRA)
    assert lim.espera("d", REGRA) == 0


def test_email_enorme_vira_chave_curta(db, cliente):
    cliente.post("/aluno/login", json={"email": "x" * 100_000 + "@teste.local", "senha": "errada123"})
    assert all(len(k) < 400 for k in limitador._pedidos)

