"""Funil da turma lido do banco: o que entra na conta e o que fica de fora."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.auth.student_service import create_student_token
from app.main import app as fastapi_app
from app.models.database import get_db
from app.models.orm import (
    Acesso, Enrollment, ExercicioGerado, Exam, Professor, Question, Student, Submission,
    TentativaDeTreino, Turma,
)
from app.services.funil_service import funil_da_turma, funil_geral

# Quarta-feira. A semana atual começa em 2026-10-26 e a última completa em 2026-10-19.
AGORA = datetime(2026, 10, 28, 12, 0)
ERRO_COMUM = "Violação de Estrutura"


def _turma(db, professor, nome="CS1 A", alunos_previstos=None):
    turma = Turma(nome=nome, codigo="CS1", professor_id=professor.id,
                  alunos_previstos=alunos_previstos)
    db.add(turma)
    db.commit()
    db.refresh(turma)
    return turma


def _atividade(db, turma, publicada=True, modo="prova", abre_em=None, fecha_em=None,
               max_tentativas=None):
    exam = Exam(filename="lista.pdf", raw_text="", turma_id=turma.id, publicada=publicada,
                modo=modo, abre_em=abre_em, fecha_em=fecha_em, max_tentativas=max_tentativas)
    db.add(exam)
    db.flush()
    questao = Question(exam_id=exam.id, number="1", statement="Enunciado")
    db.add(questao)
    db.commit()
    db.refresh(questao)
    return questao


def _aluno(db, email, nome, turmas, entrada=AGORA - timedelta(days=20), origem=None):
    aluno = Student(email=email, nome=nome, senha_hash="x")
    db.add(aluno)
    db.flush()
    for turma in turmas:
        db.add(Enrollment(student_id=aluno.id, turma_id=turma.id, created_at=entrada,
                          origem=origem))
    db.commit()
    db.refresh(aluno)
    return aluno


def _envio(db, aluno, questao, categoria, momento):
    db.add(Submission(question_id=questao.id, student_id=aluno.id if aluno else None,
                      matricula=None if aluno else "2026001", code="int main(){return 0;}",
                      error_category=categoria, submitted_at=momento))
    db.commit()


def _treino(db, aluno, passou, momento, exercicio=None):
    if exercicio is None:
        exercicio = ExercicioGerado(student_id=aluno.id, error_category=ERRO_COMUM,
                                    titulo="Treino", enunciado="Enunciado", casos_teste=[])
        db.add(exercicio)
        db.flush()
    db.add(TentativaDeTreino(exercicio_id=exercicio.id, student_id=aluno.id,
                             code="int main(){return 0;}", all_tests_passed=passou,
                             error_category="" if passou else ERRO_COMUM, submitted_at=momento))
    db.commit()
    return exercicio


def _acesso(db, aluno, momento, via=None):
    db.add(Acesso(student_id=aluno.id, momento=momento, via=via))
    db.commit()


def _nomes(saude):
    return [a["nome"] for a in saude["vermelho"]], [a["nome"] for a in saude["amarelo"]]


class TestFunilDaTurma:
    def test_conta_erro_corrigido_da_lista_e_da_trilha(self, db, professor):
        turma = _turma(db, professor)
        questao = _atividade(db, turma)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=1))
        _envio(db, ana, questao, "Correto", AGORA - timedelta(hours=2))
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=1))
        _treino(db, ana, True, AGORA - timedelta(hours=1), exercicio=exercicio)

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["turma_id"] == turma.id
        assert funil["gerado_em"] == AGORA.isoformat()
        assert funil["north_star"]["total"] == 2
        assert funil["north_star"]["semana_atual"] == 2

    def test_envio_sem_conta_fica_fora(self, db, professor):
        turma = _turma(db, professor)
        questao = _atividade(db, turma)
        _aluno(db, "ana@teste.com", "Ana", [turma])
        _envio(db, None, questao, ERRO_COMUM, AGORA - timedelta(days=1))
        _envio(db, None, questao, "Correto", AGORA - timedelta(hours=2))

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["north_star"]["total"] == 0
        assert funil["ativacao"]["com_primeiro_envio"] == 0

    def test_atividade_nao_publicada_fica_fora(self, db, professor):
        turma = _turma(db, professor)
        rascunho = _atividade(db, turma, publicada=False)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        _envio(db, ana, rascunho, ERRO_COMUM, AGORA - timedelta(days=1))
        _envio(db, ana, rascunho, "Correto", AGORA - timedelta(hours=2))

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["north_star"]["total"] == 0
        assert _nomes(funil["saude"]) == ([], [])

    def test_atividade_encerrada_ou_agendada_nao_deixa_pendente(self, db, professor):
        turma = _turma(db, professor)
        _atividade(db, turma, fecha_em=AGORA - timedelta(days=1))
        _atividade(db, turma, abre_em=AGORA + timedelta(days=1))
        _aluno(db, "ana@teste.com", "Ana", [turma])

        assert _nomes(funil_da_turma(turma, db, agora=AGORA)["saude"]) == ([], [])

        _atividade(db, turma)
        assert _nomes(funil_da_turma(turma, db, agora=AGORA)["saude"]) == (["Ana"], [])

    @pytest.mark.parametrize("teto, vermelhos", [(2, []), (3, ["Ana"])])
    def test_teto_de_tentativas_gasto_tira_a_questao(self, db, professor, teto, vermelhos):
        turma = _turma(db, professor)
        questao = _atividade(db, turma, max_tentativas=teto)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=AGORA - timedelta(days=30))
        _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=20))
        _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=20, minutes=-1))

        assert _nomes(funil_da_turma(turma, db, agora=AGORA)["saude"])[0] == vermelhos

    def test_tamanho_da_turma_e_atividade_de_treino(self, db, professor):
        turma = _turma(db, professor, alunos_previstos=4)
        questao = _atividade(db, turma, modo="treino")
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=AGORA - timedelta(days=30))
        _envio(db, ana, questao, ERRO_COMUM, datetime(2026, 10, 14, 10))
        _envio(db, ana, questao, ERRO_COMUM, datetime(2026, 10, 20, 10))

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["aquisicao"]["alunos_previstos"] == 4
        assert funil["aquisicao"]["taxa_matriculados"] == 25.0
        ultima = funil["retencao"]["ultima_completa"]
        assert ultima["semana"] == "2026-10-19"
        assert ultima["voltaram_por_envio"] == 1
        assert ultima["por_conta_propria"] == 1


class TestNorthStarPorTipo:
    def test_separa_provas_listas_e_trilha(self, db, professor):
        turma = _turma(db, professor)
        prova = _atividade(db, turma, modo="prova")
        lista = _atividade(db, turma, modo="treino")
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        for questao in (prova, lista):
            _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=1))
            _envio(db, ana, questao, "Correto", AGORA - timedelta(hours=2))
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=1))
        _treino(db, ana, True, AGORA - timedelta(hours=1), exercicio=exercicio)
        acertou_de_primeira = _atividade(db, turma, modo="treino")
        _envio(db, ana, acertou_de_primeira, "Correto", AGORA - timedelta(hours=1))

        north_star = funil_da_turma(turma, db, agora=AGORA)["north_star"]

        assert north_star["total"] == 3
        assert north_star["por_tipo"] == {"provas": 1, "listas": 1, "trilha": 1}


class TestFiltroPelaMatricula:
    def test_trilha_de_antes_da_matricula_fica_fora_da_turma(self, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=AGORA - timedelta(days=2))
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=5))
        _treino(db, ana, True, AGORA - timedelta(days=4), exercicio=exercicio)

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["north_star"]["total"] == 0
        assert funil["ativacao"]["com_primeiro_envio"] == 0

    def test_trilha_entre_duas_matriculas_conta_so_na_turma_em_que_ja_estava(self, db, professor):
        a = _turma(db, professor, "CS1 A")
        b = _turma(db, professor, "CS1 B")
        ana = _aluno(db, "ana@teste.com", "Ana", [a], entrada=AGORA - timedelta(days=10))
        db.add(Enrollment(student_id=ana.id, turma_id=b.id, created_at=AGORA - timedelta(days=2)))
        db.commit()
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=5))
        _treino(db, ana, True, AGORA - timedelta(days=4), exercicio=exercicio)

        assert funil_da_turma(a, db, agora=AGORA)["north_star"]["total"] == 1
        assert funil_da_turma(b, db, agora=AGORA)["north_star"]["total"] == 0
        assert funil_geral(db, agora=AGORA)["total"]["north_star"]["total"] == 1

    def test_lista_religada_de_antes_da_matricula_conta_na_north_star_e_nao_no_sucesso(
            self, db, professor):
        turma = _turma(db, professor)
        questao = _atividade(db, turma)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=AGORA - timedelta(days=2))
        _envio(db, ana, questao, ERRO_COMUM, AGORA - timedelta(days=5))
        _envio(db, ana, questao, "Correto", AGORA - timedelta(days=4))

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["north_star"]["total"] == 1
        assert funil["sucesso"]["chegaram"] == 0

    def test_acesso_de_antes_da_matricula_nao_conta_na_retencao(self, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], entrada=datetime(2026, 10, 21))
        _acesso(db, ana, datetime(2026, 10, 15, 10))
        _acesso(db, ana, datetime(2026, 10, 22, 10))

        ultima = funil_da_turma(turma, db, agora=AGORA)["retencao"]["ultima_completa"]

        assert ultima["base"] == 1
        assert ultima["voltaram"] == 0


class TestRetencaoPeloAcesso:
    def test_voltou_pelo_acesso_com_os_sinais(self, db, professor):
        turma = _turma(db, professor)
        # A prova puxa de 2026-10-20 08:00 até 2026-10-23 10:00.
        prova = _atividade(db, turma, abre_em=datetime(2026, 10, 23, 8),
                           fecha_em=datetime(2026, 10, 23, 10))
        # Treino e rascunho com data cobririam 2026-10-19, mas não puxam.
        _atividade(db, turma, modo="treino", abre_em=datetime(2026, 10, 19),
                   fecha_em=datetime(2026, 10, 25))
        _atividade(db, turma, publicada=False, abre_em=datetime(2026, 10, 19, 12),
                   fecha_em=datetime(2026, 10, 25))
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        bia = _aluno(db, "bia@teste.com", "Bia", [turma])
        caio = _aluno(db, "caio@teste.com", "Caio", [turma])
        _acesso(db, ana, datetime(2026, 10, 14, 10))
        _acesso(db, ana, datetime(2026, 10, 21, 10))
        _acesso(db, bia, datetime(2026, 10, 14, 10))
        _acesso(db, bia, datetime(2026, 10, 19, 9), via="convite")
        _envio(db, caio, prova, ERRO_COMUM, datetime(2026, 10, 14, 10))
        _envio(db, caio, prova, ERRO_COMUM, datetime(2026, 10, 20, 10))

        ultima = funil_da_turma(turma, db, agora=AGORA)["retencao"]["ultima_completa"]

        assert ultima["semana"] == "2026-10-19"
        assert ultima["base"] == 3
        assert ultima["voltaram"] == 2
        assert ultima["taxa"] == 66.7
        assert ultima["sem_prova_marcada"] == 1
        assert ultima["sem_aviso"] == 1
        assert ultima["voltaram_por_envio"] == 1
        assert ultima["taxa_por_envio"] == 33.3

    def test_matriculas_por_origem(self, db, professor):
        turma = _turma(db, professor)
        _aluno(db, "ana@teste.com", "Ana", [turma], origem="convite")
        _aluno(db, "bia@teste.com", "Bia", [turma], origem="codigo")
        _aluno(db, "caio@teste.com", "Caio", [turma])

        funil = funil_da_turma(turma, db, agora=AGORA)

        assert funil["aquisicao"]["por_origem"] == {"convite": 1, "codigo": 1, "sem_origem": 1}


class TestFunilGeral:
    def test_treino_de_aluno_em_duas_turmas_conta_uma_vez_no_total(self, db, professor):
        a = _turma(db, professor, "CS1 A")
        b = _turma(db, professor, "CS1 B")
        ana = _aluno(db, "ana@teste.com", "Ana", [a, b])
        exercicio = _treino(db, ana, False, AGORA - timedelta(days=1))
        _treino(db, ana, True, AGORA - timedelta(hours=1), exercicio=exercicio)

        assert funil_da_turma(a, db, agora=AGORA)["north_star"]["total"] == 1
        assert funil_da_turma(b, db, agora=AGORA)["north_star"]["total"] == 1
        geral = funil_geral(db, agora=AGORA)
        assert geral["total"]["north_star"]["total"] == 1
        assert geral["total"]["matriculados"] == 1
        assert [t["north_star_total"] for t in geral["por_turma"]] == [1, 1]

    def test_professores_e_turmas_com_matricula(self, db, professor):
        a = _turma(db, professor, "CS1 A", alunos_previstos=30)
        _turma(db, professor, "CS1 B")
        _aluno(db, "ana@teste.com", "Ana", [a])

        geral = funil_geral(db, agora=AGORA)

        assert geral["total"]["professores_com_turma"] == 1
        assert geral["total"]["turmas_com_matricula"] == 1
        assert [t["nome"] for t in geral["por_turma"]] == ["CS1 A", "CS1 B"]
        assert geral["por_turma"][0]["professor"] == "Professor Teste"
        assert geral["por_turma"][0]["alunos_previstos"] == 30
        assert geral["total"]["retencao_ultima_semana"]["semana"] == "2026-10-19"

    def test_total_e_linhas_trazem_os_campos_novos(self, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma], origem="convite")
        _acesso(db, ana, datetime(2026, 10, 14, 10))
        _acesso(db, ana, datetime(2026, 10, 21, 10))

        geral = funil_geral(db, agora=AGORA)

        semana = geral["total"]["retencao_ultima_semana"]
        assert set(semana) == {"semana", "base", "voltaram", "taxa", "voltaram_por_envio",
                               "taxa_por_envio"}
        assert semana["voltaram"] == 1
        linha = geral["por_turma"][0]
        assert linha["taxa_retencao"] == 100.0
        assert linha["taxa_retencao_envio"] == 0.0
        assert linha["por_origem"] == {"convite": 1, "codigo": 0, "sem_origem": 0}
        assert linha["taxa_sucesso_na_sessao"] == 0.0

    def test_base_vazia(self, db):
        geral = funil_geral(db, agora=AGORA)
        assert geral["por_turma"] == []
        assert geral["total"]["matriculados"] == 0
        assert geral["total"]["taxa_ativacao"] is None
        assert geral["total"]["north_star"]["total"] == 0


@pytest.fixture()
def anonimo(db):
    """Cliente sem professor injetado: quem decide é a autenticação de verdade."""
    def override_get_db():
        yield db

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


class TestRota:
    def test_dono_recebe_o_funil(self, client, db, professor):
        turma = _turma(db, professor)
        _atividade(db, turma)
        _aluno(db, "ana@teste.com", "Ana Lima", [turma],
               entrada=datetime.utcnow() - timedelta(days=20))

        resp = client.get(f"/turmas/{turma.id}/funil")

        assert resp.status_code == 200
        corpo = resp.json()
        assert corpo["turma_id"] == turma.id
        assert len(corpo["north_star"]["semanas"]) == 8
        assert len(corpo["retencao"]["semanas"]) == 8
        assert corpo["aquisicao"]["meta"] == 80.0
        assert corpo["saude"]["vermelho"][0]["nome"] == "Ana Lima"
        assert corpo["saude"]["vermelho"][0]["ultimo_envio"] is None
        assert corpo["protecao"]["itens_com_acerto"] == 0
        assert corpo["aquisicao"]["por_origem"] == {"convite": 0, "codigo": 0, "sem_origem": 1}
        assert {"sem_prova_marcada", "taxa_sem_aviso", "voltaram_por_envio",
                "taxa_por_envio"} <= set(corpo["retencao"]["ultima_completa"])
        assert corpo["sucesso"]["ainda_nao_chegaram"] == 1
        assert corpo["sucesso"]["mediana_minutos"] is None

    def test_turma_de_outro_professor_da_404(self, client, db):
        outro = Professor(email="outro@teste.com", nome="Outro Professor", senha_hash="x")
        db.add(outro)
        db.commit()
        turma = _turma(db, outro)
        assert client.get(f"/turmas/{turma.id}/funil").status_code == 404

    def test_token_de_aluno_da_401(self, anonimo, db, professor):
        turma = _turma(db, professor)
        ana = _aluno(db, "ana@teste.com", "Ana", [turma])
        token = create_student_token(ana.id)
        resp = anonimo.get(f"/turmas/{turma.id}/funil",
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401

    def test_sem_token_da_401(self, anonimo, db, professor):
        turma = _turma(db, professor)
        assert anonimo.get(f"/turmas/{turma.id}/funil").status_code == 401
