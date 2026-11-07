"""Prova chegando (experimento 5): qual prova entra no cartão e quais erros ele mostra."""
from datetime import datetime, timedelta

from app.services.historico_do_aluno import ACERTO, ERRO, LISTA, TRILHA, Envio, erros_do_aluno
from app.services.inicio_service import AtividadeDoPainel
from app.services.prova_chegando import (
    erros_do_treino, montar_cartao, primeiro_pendente, prova_na_janela,
)

AGORA = datetime(2026, 11, 4, 12, 0)


def _atividade(exam_id=1, abre_em=AGORA + timedelta(days=2), modo="prova", situacao="agendada",
               com_o_que_fazer=True):
    return AtividadeDoPainel(
        exam_id=exam_id, titulo=f"Prova {exam_id}", turma_nome="Turma A", modo=modo,
        situacao=situacao, abre_em=abre_em, fecha_em=None, criada_em=AGORA,
        com_o_que_fazer=com_o_que_fazer)


class TestProvaNaJanela:
    def test_exatamente_3_dias_antes_entra(self):
        prova = _atividade(abre_em=AGORA + timedelta(days=3))
        assert prova_na_janela([prova], AGORA) is prova

    def test_um_segundo_antes_de_a_janela_comecar_nao_entra(self):
        prova = _atividade(abre_em=AGORA + timedelta(days=3, seconds=1))
        assert prova_na_janela([prova], AGORA) is None

    def test_um_segundo_antes_de_abrir_entra(self):
        prova = _atividade(abre_em=AGORA + timedelta(seconds=1))
        assert prova_na_janela([prova], AGORA) is prova

    def test_no_instante_de_abrir_nao_entra(self):
        assert prova_na_janela([_atividade(abre_em=AGORA, situacao="aberta")], AGORA) is None

    def test_sem_abre_em_nao_entra(self):
        assert prova_na_janela([_atividade(abre_em=None, situacao="aberta")], AGORA) is None

    def test_lista_nao_entra(self):
        assert prova_na_janela([_atividade(modo="treino")], AGORA) is None

    def test_sem_o_que_fazer_nao_entra(self):
        assert prova_na_janela([_atividade(com_o_que_fazer=False)], AGORA) is None

    def test_encerrada_nao_entra(self):
        assert prova_na_janela([_atividade(situacao="encerrada")], AGORA) is None

    def test_duas_na_janela_vale_a_que_abre_primeiro(self):
        depois = _atividade(exam_id=1, abre_em=AGORA + timedelta(days=2))
        antes = _atividade(exam_id=2, abre_em=AGORA + timedelta(days=1))
        assert prova_na_janela([depois, antes], AGORA) is antes

    def test_empate_vale_o_menor_id(self):
        maior = _atividade(exam_id=9)
        menor = _atividade(exam_id=3)
        assert prova_na_janela([maior, menor], AGORA) is menor


INICIO = AGORA - timedelta(days=1)


def _errou(categoria, minuto):
    return Envio(origem=LISTA, item_id=1, momento=INICIO + timedelta(minutes=minuto),
                 categoria=categoria, resultado=ERRO, o_que_fazer="Revise.")


def _acertou(alvo, minuto, categoria="Correto"):
    return Envio(origem=TRILHA, item_id=9, momento=INICIO + timedelta(minutes=minuto),
                 categoria=categoria, resultado=ACERTO, alvo=alvo)


def _lista(envios):
    return erros_do_treino(erros_do_aluno(envios), envios, INICIO)


class TestErrosDoTreino:
    def test_so_ativos_por_frequencia_cortados_em_3(self):
        envios = [_errou("A", -40), _errou("A", -39), _errou("A", -38),
                  _errou("B", -37), _errou("B", -36), _errou("C", -35), _errou("D", -34)]
        assert _lista(envios) == [
            {"error_category": "A", "feito": False},
            {"error_category": "B", "feito": False},
            {"error_category": "C", "feito": False},
        ]

    def test_acerto_na_janela_vira_feito_e_vem_primeiro(self):
        envios = [_errou("A", -40), _errou("A", -39), _errou("A", -38), _errou("B", -37),
                  _acertou("B", 5)]
        assert _lista(envios) == [
            {"error_category": "B", "feito": True},
            {"error_category": "A", "feito": False},
        ]

    def test_acerto_antes_da_janela_nao_conta(self):
        envios = [_errou("A", -300), _acertou("A", -200), _errou("B", -100)]
        assert _lista(envios) == [{"error_category": "B", "feito": False}]

    def test_acerto_com_a_categoria_do_alvo_nao_conta(self):
        envios = [_errou("A", -40), _acertou("A", 5, categoria="A")]
        assert _lista(envios) == [{"error_category": "A", "feito": False}]

    def test_erro_feito_que_reaparece_continua_feito(self):
        envios = [_errou("A", -40), _acertou("A", 5), _errou("A", 6)]
        assert _lista(envios) == [{"error_category": "A", "feito": True}]

    def test_sem_erros_a_lista_fica_vazia(self):
        assert _lista([]) == []

    def test_acerto_para_outra_categoria_nao_marca_esta(self):
        envios = [_errou("A", -40), _errou("B", -39), _acertou("B", 5)]
        assert _lista(envios) == [
            {"error_category": "B", "feito": True},
            {"error_category": "A", "feito": False},
        ]

    def test_acerto_de_alvo_que_o_aluno_nunca_errou_nao_entra(self):
        envios = [_errou("A", -40), _acertou("Z", 5)]
        assert _lista(envios) == [{"error_category": "A", "feito": False}]

    def test_superado_antes_da_janela_entra_se_treinar_de_novo(self):
        envios = [_errou("A", -300), _acertou("A", -200), _acertou("A", 5)]
        assert _lista(envios) == [{"error_category": "A", "feito": True}]

    def test_corte_em_3_com_feitos_e_pendentes(self):
        envios = [_errou("A", -40), _errou("A", -39), _errou("B", -38), _errou("C", -37),
                  _errou("D", -36), _acertou("C", 5), _acertou("D", 6)]
        assert _lista(envios) == [
            {"error_category": "C", "feito": True},
            {"error_category": "D", "feito": True},
            {"error_category": "A", "feito": False},
        ]

    def test_quatro_feitos_mostram_so_3(self):
        envios = [_errou(c, -40) for c in "ABCD"] + [
            _acertou(c, i + 1) for i, c in enumerate("ABCD")]
        assert [e["error_category"] for e in _lista(envios)] == ["A", "B", "C"]

    def test_feitos_em_ordem_do_acerto(self):
        envios = [_errou("A", -40), _errou("B", -39), _acertou("B", 5), _acertou("A", 6)]
        assert [e["error_category"] for e in _lista(envios)] == ["B", "A"]


class TestCartao:
    def test_monta_o_cartao(self):
        prova = _atividade(exam_id=7, abre_em=AGORA + timedelta(days=2))
        envios = [_errou("A", -40)]
        assert montar_cartao(prova, erros_do_aluno(envios), envios) == {
            "exam_id": 7, "titulo": "Prova 7", "turma_nome": "Turma A",
            "abre_em": (AGORA + timedelta(days=2)).isoformat(),
            "erros": [{"error_category": "A", "feito": False}],
        }

    def test_sem_erro_para_mostrar_nao_ha_cartao(self):
        assert montar_cartao(_atividade(), [], []) is None

    def test_primeiro_pendente_pula_os_feitos(self):
        cartao = {"erros": [{"error_category": "B", "feito": True},
                            {"error_category": "A", "feito": False}]}
        assert primeiro_pendente(cartao) == "A"

    def test_sem_pendente_devolve_vazio(self):
        assert primeiro_pendente({"erros": [{"error_category": "B", "feito": True}]}) is None

