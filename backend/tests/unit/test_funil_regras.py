"""Regras do funil sobre registros montados à mão, sem banco."""
import itertools
from datetime import datetime, timedelta

from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Matricula, Tentativa, aquisicao, ativacao,
    erros_corrigidos, north_star, protecao, resultado_da_lista, resultado_da_trilha,
    retencao, retencao_da_semana, ultimas_semanas,
)

# Quarta-feira. A semana atual começa em 2026-10-26.
AGORA = datetime(2026, 10, 28, 12, 0)
_ids = itertools.count(1)


def tent(resultado, momento, aluno=1, item=10, origem=LISTA, por_conta_propria=False):
    return Tentativa(aluno=aluno, origem=origem, item_id=item, momento=momento,
                     ordem=next(_ids), resultado=resultado, por_conta_propria=por_conta_propria)


def mat(aluno, entrada, nome="Aluno"):
    return Matricula(aluno=aluno, nome=nome, entrada=entrada)


def _por_semana(ns):
    return {s["semana"]: s["erros_corrigidos"] for s in ns["semanas"]}


class TestResultado:
    def test_lista(self):
        assert resultado_da_lista("Correto") == ACERTO
        assert resultado_da_lista("Erro Desconhecido") == FALHA
        assert resultado_da_lista("") == FALHA
        assert resultado_da_lista(None) == FALHA
        assert resultado_da_lista("Violação de Estrutura") == ERRO

    def test_trilha(self):
        assert resultado_da_trilha(True, "") == ACERTO
        assert resultado_da_trilha(False, "Erro Desconhecido") == FALHA
        assert resultado_da_trilha(None, "") == FALHA
        assert resultado_da_trilha(False, "Violação de Estrutura") == ERRO


class TestSemanas:
    def test_oito_semanas_terminando_na_atual(self):
        semanas = ultimas_semanas(AGORA)
        assert len(semanas) == 8
        assert semanas[0] == "2026-09-07"
        assert semanas[-1] == "2026-10-26"

    def test_sem_correcao_as_oito_semanas_vem_com_zero(self):
        ns = north_star([], AGORA)
        assert len(ns["semanas"]) == 8
        assert all(s["erros_corrigidos"] == 0 for s in ns["semanas"])
        assert ns["semana_atual"] == 0
        assert ns["total"] == 0


class TestErrosCorrigidos:
    def test_errou_e_acertou_conta_um_na_semana_do_acerto(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 16)), tent(ACERTO, datetime(2026, 10, 27))]
        ns = north_star(erros_corrigidos(tentativas), AGORA)
        assert ns["semana_atual"] == 1
        assert ns["total"] == 1
        assert _por_semana(ns)["2026-10-12"] == 0

    def test_acertou_de_primeira_nao_conta(self):
        assert erros_corrigidos([tent(ACERTO, datetime(2026, 10, 27))]) == []

    def test_errou_acertou_errou_e_acertou_de_novo_conta_um(self):
        tentativas = [
            tent(ERRO, datetime(2026, 10, 20)), tent(ACERTO, datetime(2026, 10, 21)),
            tent(ERRO, datetime(2026, 10, 26)), tent(ACERTO, datetime(2026, 10, 27)),
        ]
        corrigidos = erros_corrigidos(tentativas)
        assert corrigidos == [(1, datetime(2026, 10, 21))]

    def test_so_errou_nao_conta(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 26)), tent(ERRO, datetime(2026, 10, 27))]
        assert erros_corrigidos(tentativas) == []

    def test_falha_tecnica_antes_do_acerto_nao_conta(self):
        tentativas = [tent(FALHA, datetime(2026, 10, 26)), tent(ACERTO, datetime(2026, 10, 27))]
        assert erros_corrigidos(tentativas) == []

    def test_falha_tecnica_entre_o_erro_e_o_acerto_nao_atrapalha(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 26)), tent(FALHA, datetime(2026, 10, 26, 1)),
                      tent(ACERTO, datetime(2026, 10, 27))]
        assert len(erros_corrigidos(tentativas)) == 1

    def test_trilha_conta(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 26), origem=TRILHA),
                      tent(ACERTO, datetime(2026, 10, 27), origem=TRILHA)]
        assert len(erros_corrigidos(tentativas)) == 1

    def test_mesmo_id_na_lista_e_na_trilha_sao_itens_diferentes(self):
        tentativas = [
            tent(ERRO, datetime(2026, 10, 26), origem=LISTA), tent(ACERTO, datetime(2026, 10, 27), origem=LISTA),
            tent(ERRO, datetime(2026, 10, 26), origem=TRILHA), tent(ACERTO, datetime(2026, 10, 27), origem=TRILHA),
        ]
        assert len(erros_corrigidos(tentativas)) == 2

    def test_a_ordem_vem_do_momento_e_nao_da_lista(self):
        tentativas = [tent(ACERTO, datetime(2026, 10, 27)), tent(ERRO, datetime(2026, 10, 26))]
        assert len(erros_corrigidos(tentativas)) == 1


class TestProtecao:
    def test_media_ate_acertar_e_acerto_de_primeira(self):
        tentativas = [
            tent(ERRO, datetime(2026, 10, 20), item=1), tent(ERRO, datetime(2026, 10, 21), item=1),
            tent(ACERTO, datetime(2026, 10, 22), item=1),
            tent(ACERTO, datetime(2026, 10, 20), item=2),
            tent(ERRO, datetime(2026, 10, 20), item=3),
        ]
        p = protecao(tentativas)
        assert p["media_tentativas_ate_acertar"] == 2.0
        assert p["acerto_de_primeira"] == 33.3
        assert p["itens_com_acerto"] == 2

    def test_falha_tecnica_nao_entra_na_conta(self):
        p = protecao([tent(FALHA, datetime(2026, 10, 20)), tent(ACERTO, datetime(2026, 10, 21))])
        assert p["media_tentativas_ate_acertar"] == 1.0
        assert p["acerto_de_primeira"] == 100.0

    def test_so_falha_tecnica_deixa_tudo_nulo(self):
        p = protecao([tent(FALHA, datetime(2026, 10, 20))])
        assert p == {"media_tentativas_ate_acertar": None, "acerto_de_primeira": None,
                     "itens_com_acerto": 0}


DIA0 = datetime(2026, 10, 1, 10, 0)


class TestAquisicao:
    def test_sem_o_tamanho_da_turma_as_taxas_ficam_nulas(self):
        a = aquisicao([mat(1, DIA0), mat(2, DIA0)], None)
        assert a["matriculados"] == 2
        assert a["alunos_previstos"] is None
        assert a["taxa_matriculados"] is None
        assert a["taxa_primeira_semana"] is None
        assert a["meta"] == 80.0

    def test_primeira_semana_conta_ate_sete_dias_da_primeira_matricula(self):
        matriculas = [mat(1, DIA0), mat(2, DIA0 + timedelta(days=7)), mat(3, DIA0 + timedelta(days=8))]
        a = aquisicao(matriculas, 4)
        assert a["primeira_semana"] == 2
        assert a["taxa_primeira_semana"] == 50.0
        assert a["taxa_matriculados"] == 75.0

    def test_turma_vazia(self):
        a = aquisicao([], 10)
        assert a["matriculados"] == 0
        assert a["primeira_semana"] == 0
        assert a["taxa_matriculados"] == 0.0


class TestAtivacao:
    def test_ativa_quem_corrige_ate_sete_dias_depois_de_entrar(self):
        matriculas = [mat(1, DIA0), mat(2, DIA0), mat(3, DIA0)]
        tentativas = [
            tent(ERRO, DIA0 + timedelta(days=1), aluno=1),
            tent(ACERTO, DIA0 + timedelta(days=7), aluno=1),
            tent(ERRO, DIA0 + timedelta(days=1), aluno=2),
            tent(ACERTO, DIA0 + timedelta(days=8), aluno=2),
            tent(ACERTO, DIA0 + timedelta(days=1), aluno=3),
        ]
        a = ativacao(matriculas, tentativas, erros_corrigidos(tentativas))
        assert a["matriculados"] == 3
        assert a["com_primeiro_envio"] == 3
        assert a["ativados"] == 1
        assert a["taxa"] == 33.3
        assert a["meta"] == 60.0

    def test_correcao_antes_da_matricula_nao_ativa(self):
        tentativas = [tent(ERRO, DIA0, origem=TRILHA), tent(ACERTO, DIA0 + timedelta(days=1), origem=TRILHA)]
        a = ativacao([mat(1, DIA0 + timedelta(days=5))], tentativas, erros_corrigidos(tentativas))
        assert a["ativados"] == 0

    def test_envio_de_quem_nao_esta_matriculado_nao_conta(self):
        a = ativacao([mat(1, DIA0)], [tent(ERRO, DIA0, aluno=99)], [])
        assert a["com_primeiro_envio"] == 0

    def test_falha_tecnica_conta_como_envio(self):
        a = ativacao([mat(1, DIA0)], [tent(FALHA, DIA0 + timedelta(days=1))], [])
        assert a["com_primeiro_envio"] == 1


class TestRetencao:
    def test_voltou_e_por_conta_propria_na_semana(self):
        matriculas = [mat(1, DIA0), mat(2, DIA0), mat(3, DIA0), mat(4, datetime(2026, 10, 27))]
        tentativas = [
            tent(ERRO, datetime(2026, 10, 14), aluno=1),
            tent(ERRO, datetime(2026, 10, 20), aluno=1),
            tent(ERRO, datetime(2026, 10, 21), aluno=2),
            tent(ERRO, datetime(2026, 10, 10), aluno=3),
            tent(ERRO, datetime(2026, 10, 22), aluno=3, por_conta_propria=True),
            tent(ERRO, datetime(2026, 10, 10), aluno=4),
            tent(ERRO, datetime(2026, 10, 22), aluno=4),
        ]
        s = retencao_da_semana("2026-10-19", matriculas, tentativas)
        assert s["base"] == 3
        assert s["voltaram"] == 2
        assert s["por_conta_propria"] == 1
        assert s["taxa"] == 66.7
        assert s["taxa_por_conta_propria"] == 33.3

    def test_por_conta_propria_tambem_pede_envio_antes(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 20), por_conta_propria=True)]
        s = retencao_da_semana("2026-10-19", [mat(1, DIA0)], tentativas)
        assert s["voltaram"] == 0
        assert s["por_conta_propria"] == 0

    def test_base_zero_da_taxa_nula(self):
        s = retencao_da_semana("2026-10-19", [], [])
        assert s["taxa"] is None
        assert s["taxa_por_conta_propria"] is None

    def test_cartao_usa_a_ultima_semana_completa(self):
        r = retencao([mat(1, DIA0)], [], AGORA)
        assert len(r["semanas"]) == 8
        assert r["semanas"][-1]["semana"] == "2026-10-26"
        assert r["ultima_completa"]["semana"] == "2026-10-19"
        assert r["meta"] == 50.0
