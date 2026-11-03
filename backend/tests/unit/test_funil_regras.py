"""Regras do funil sobre registros montados à mão, sem banco."""
import itertools
from datetime import datetime, timedelta

from app.services.funil_regras import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Acesso, DadosDaTurma, Matricula, Tentativa,
    aquisicao, ativacao, com_prova_marcada, erros_corrigidos, janela_da_prova,
    montar_funil, north_star, por_origem, protecao, resultado_da_lista,
    resultado_da_trilha, retencao, retencao_da_semana, saude, ultimas_semanas,
)

# Quarta-feira. A semana atual começa em 2026-10-26.
AGORA = datetime(2026, 10, 28, 12, 0)
_ids = itertools.count(1)


def tent(resultado, momento, aluno=1, item=10, origem=LISTA, por_conta_propria=False):
    return Tentativa(aluno=aluno, origem=origem, item_id=item, momento=momento,
                     ordem=next(_ids), resultado=resultado, por_conta_propria=por_conta_propria)


def mat(aluno, entrada, nome="Aluno", origem=None):
    return Matricula(aluno=aluno, nome=nome, entrada=entrada, origem=origem)


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


class TestPorOrigem:
    def test_conta_as_tres_origens(self):
        matriculas = [mat(1, DIA0, origem="convite"), mat(2, DIA0, origem="convite"),
                      mat(3, DIA0, origem="codigo"), mat(4, DIA0)]
        esperado = {"convite": 2, "codigo": 1, "sem_origem": 1}
        assert por_origem(matriculas) == esperado
        assert aquisicao(matriculas, None)["por_origem"] == esperado

    def test_turma_vazia(self):
        assert por_origem([]) == {"convite": 0, "codigo": 0, "sem_origem": 0}


ABRE = datetime(2026, 10, 20, 8, 0)
FECHA = datetime(2026, 10, 20, 10, 0)


class TestProvaQuePuxa:
    def test_com_as_duas_datas_puxa_de_tres_dias_antes_ate_o_fechamento(self):
        janelas = [janela_da_prova(ABRE, FECHA)]
        assert com_prova_marcada(ABRE - timedelta(days=3), janelas)
        assert com_prova_marcada(FECHA, janelas)
        assert not com_prova_marcada(ABRE - timedelta(days=3, seconds=1), janelas)
        assert not com_prova_marcada(FECHA + timedelta(seconds=1), janelas)

    def test_so_com_abertura_puxa_dali_em_diante(self):
        janelas = [janela_da_prova(ABRE, None)]
        assert not com_prova_marcada(ABRE - timedelta(days=4), janelas)
        assert com_prova_marcada(ABRE + timedelta(days=60), janelas)

    def test_so_com_fechamento_puxa_ate_ele(self):
        janelas = [janela_da_prova(None, FECHA)]
        assert com_prova_marcada(FECHA - timedelta(days=60), janelas)
        assert not com_prova_marcada(FECHA + timedelta(seconds=1), janelas)

    def test_sem_datas_nao_tem_janela(self):
        assert janela_da_prova(None, None) is None
        assert not com_prova_marcada(ABRE, [])

    def test_basta_uma_prova_puxar(self):
        outra = janela_da_prova(datetime(2026, 11, 10), datetime(2026, 11, 10, 2))
        janelas = [janela_da_prova(ABRE, FECHA), outra]
        assert com_prova_marcada(datetime(2026, 11, 8), janelas)
        assert not com_prova_marcada(datetime(2026, 11, 1), janelas)


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


SEMANA = "2026-10-19"
ANTES = datetime(2026, 10, 14, 10)
NA_SEMANA = datetime(2026, 10, 21, 10)


def ac(aluno, momento, via=None):
    return Acesso(aluno=aluno, momento=momento, via=via)


class TestRetencao:
    def test_pelo_envio_e_por_conta_propria_na_semana(self):
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
        s = retencao_da_semana(SEMANA, matriculas, tentativas, [], [])
        assert s["base"] == 3
        assert s["voltaram_por_envio"] == 2
        assert s["por_conta_propria"] == 1
        assert s["taxa_por_envio"] == 66.7
        assert s["taxa_por_conta_propria"] == 33.3
        assert s["voltaram"] == 0

    def test_por_conta_propria_tambem_pede_envio_antes(self):
        tentativas = [tent(ERRO, datetime(2026, 10, 20), por_conta_propria=True)]
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], tentativas, [], [])
        assert s["voltaram_por_envio"] == 0
        assert s["por_conta_propria"] == 0

    def test_voltou_pelo_acesso_com_acesso_antes(self):
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], [], [ac(1, ANTES), ac(1, NA_SEMANA)], [])
        assert s["voltaram"] == 1
        assert s["taxa"] == 100.0
        assert s["voltaram_por_envio"] == 0

    def test_voltou_pelo_acesso_com_so_envio_antes(self):
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], [tent(ERRO, ANTES)], [ac(1, NA_SEMANA)], [])
        assert s["voltaram"] == 1

    def test_acesso_sem_atividade_antes_nao_conta(self):
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], [], [ac(1, NA_SEMANA)], [])
        assert s["voltaram"] == 0

    def test_envio_sem_acesso_conta_so_pelo_envio(self):
        tentativas = [tent(ERRO, ANTES), tent(ERRO, NA_SEMANA)]
        s = retencao_da_semana(SEMANA, [mat(1, DIA0)], tentativas, [], [])
        assert s["voltaram"] == 0
        assert s["voltaram_por_envio"] == 1

    def test_sem_prova_marcada_so_com_acesso_fora_das_janelas(self):
        janelas = [janela_da_prova(datetime(2026, 10, 23, 8), datetime(2026, 10, 23, 10))]
        acessos = [
            # aluno 1 só abriu dentro da janela da prova
            ac(1, ANTES), ac(1, datetime(2026, 10, 21, 10)),
            # aluno 2 abriu uma vez antes de a prova começar a puxar
            ac(2, ANTES), ac(2, datetime(2026, 10, 19, 9)), ac(2, datetime(2026, 10, 22, 9)),
        ]
        s = retencao_da_semana(SEMANA, [mat(1, DIA0), mat(2, DIA0)], [], acessos, janelas)
        assert s["voltaram"] == 2
        assert s["sem_prova_marcada"] == 1
        assert s["taxa_sem_prova_marcada"] == 50.0

    def test_sem_aviso_so_com_acesso_sem_origem(self):
        acessos = [ac(1, ANTES), ac(1, NA_SEMANA), ac(2, ANTES), ac(2, NA_SEMANA, via="convite")]
        s = retencao_da_semana(SEMANA, [mat(1, DIA0), mat(2, DIA0)], [], acessos, [])
        assert s["voltaram"] == 2
        assert s["sem_aviso"] == 1
        assert s["taxa_sem_aviso"] == 50.0

    def test_base_zero_deixa_todas_as_taxas_nulas(self):
        s = retencao_da_semana(SEMANA, [], [], [], [])
        for chave in ("taxa", "taxa_sem_prova_marcada", "taxa_sem_aviso",
                      "taxa_por_envio", "taxa_por_conta_propria"):
            assert s[chave] is None

    def test_cartao_usa_a_ultima_semana_completa(self):
        r = retencao([mat(1, DIA0)], [], [], [], AGORA)
        assert len(r["semanas"]) == 8
        assert r["semanas"][-1]["semana"] == "2026-10-26"
        assert r["ultima_completa"]["semana"] == SEMANA
        assert r["meta"] == 50.0


# Questões 10 e 11 abertas e sem teto de tentativas.
ABERTAS = {10: None, 11: None}


def _dias(n, **extra):
    return AGORA - timedelta(days=n, **extra)


def _saude(tentativas, matriculas=None, abertas=None):
    matriculas = matriculas if matriculas is not None else [mat(1, _dias(30), nome="Ana")]
    return saude(matriculas, tentativas, ABERTAS if abertas is None else abertas, AGORA)


def _cores(s):
    return ([(a["nome"], a["motivo"]) for a in s["vermelho"]],
            [(a["nome"], a["motivo"]) for a in s["amarelo"]])


class TestSaude:
    def test_mais_de_14_dias_sem_envio_e_vermelho(self):
        s = _saude([tent(ACERTO, _dias(15), item=11)])
        assert _cores(s) == ([("Ana", "Mais de 14 dias sem envio")], [])
        assert s["vermelho"][0]["dias_sem_envio"] == 15
        assert s["vermelho"][0]["ultimo_envio"] == _dias(15).isoformat()

    def test_exatamente_14_dias_ainda_e_amarelo(self):
        s = _saude([tent(ACERTO, _dias(14), item=11)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_exatamente_7_dias_ja_e_amarelo(self):
        s = _saude([tent(ACERTO, _dias(7), item=11)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_mais_de_7_dias_depois_de_errar_numa_questao_em_aberto_e_vermelho(self):
        s = _saude([tent(ERRO, _dias(8), item=10)])
        assert _cores(s) == ([("Ana", "Parou depois de errar")], [])

    def test_exatamente_7_dias_depois_de_errar_e_amarelo(self):
        s = _saude([tent(ERRO, _dias(7), item=10)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_8_dias_depois_de_acertar_e_amarelo(self):
        s = _saude([tent(ACERTO, _dias(8), item=11)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_falha_tecnica_no_fim_nao_e_parar_depois_de_errar(self):
        s = _saude([tent(FALHA, _dias(8), item=10)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_cinco_erros_numa_questao_em_aberto_e_amarelo(self):
        s = _saude([tent(ERRO, _dias(3, minutes=i), item=10) for i in range(5)])
        assert _cores(s) == ([], [("Ana", "5 erros seguidos na mesma questão")])

    def test_quatro_erros_e_6_dias_fica_fora(self):
        s = _saude([tent(ERRO, _dias(6, minutes=i), item=10) for i in range(4)])
        assert _cores(s) == ([], [])

    def test_quem_nunca_enviou_conta_desde_a_matricula(self):
        s = _saude([], matriculas=[mat(1, _dias(15), nome="Ana"), mat(2, _dias(8), nome="Bia")])
        assert _cores(s) == ([("Ana", "Mais de 14 dias sem envio")], [("Bia", "7 a 14 dias sem envio")])
        assert s["vermelho"][0]["ultimo_envio"] is None

    def test_quem_resolveu_tudo_o_que_esta_aberto_fica_fora(self):
        s = _saude([tent(ACERTO, _dias(30), item=10), tent(ACERTO, _dias(30), item=11)])
        assert _cores(s) == ([], [])

    def test_sem_questao_aberta_ninguem_fica_pendente(self):
        s = _saude([], abertas={})
        assert _cores(s) == ([], [])

    def test_teto_de_tentativas_gasto_tira_a_questao(self):
        tentativas = [tent(ERRO, _dias(20), item=10), tent(ERRO, _dias(20, minutes=-1), item=10)]
        assert _cores(_saude(tentativas, abertas={10: 2})) == ([], [])
        assert _cores(_saude(tentativas, abertas={10: 3}))[0] == [("Ana", "Mais de 14 dias sem envio")]

    def test_trilha_conta_como_envio_mas_nao_vira_motivo(self):
        tentativas = [tent(ERRO, _dias(20), item=10)]
        tentativas += [tent(ERRO, _dias(1, minutes=i), item=7, origem=TRILHA) for i in range(5)]
        assert _cores(_saude(tentativas)) == ([], [])

    def test_trilha_de_antes_da_matricula_nao_conta_como_parado(self):
        tentativas = [tent(ACERTO, _dias(30), item=7, origem=TRILHA)]
        s = _saude(tentativas, matriculas=[mat(1, _dias(2), nome="Ana")])
        assert _cores(s) == ([], [])

    def test_cinco_erros_e_8_dias_e_parou_depois_de_errar(self):
        s = _saude([tent(ERRO, _dias(8, minutes=i), item=10) for i in range(5)])
        assert _cores(s) == ([("Ana", "Parou depois de errar")], [])

    def test_cinco_erros_e_exatamente_7_dias_e_sem_envio(self):
        s = _saude([tent(ERRO, _dias(7, minutes=i), item=10) for i in range(5)])
        assert _cores(s) == ([], [("Ana", "7 a 14 dias sem envio")])

    def test_ordem_por_dias_sem_envio_e_depois_por_nome(self):
        matriculas = [mat(1, _dias(16), nome="Caio"), mat(2, _dias(20), nome="Bia"),
                      mat(3, _dias(16), nome="Ana")]
        s = _saude([], matriculas=matriculas)
        assert [a["nome"] for a in s["vermelho"]] == ["Bia", "Ana", "Caio"]

    def test_taxa_de_vermelho_sobre_os_matriculados(self):
        matriculas = [mat(1, _dias(20), nome="Ana")] + [mat(i, _dias(1), nome=f"A{i}") for i in range(2, 5)]
        s = _saude([], matriculas=matriculas)
        assert s["taxa_vermelho"] == 25.0
        assert s["meta"] == 15.0


class TestMontarFunil:
    def test_traz_os_seis_blocos(self):
        dados = DadosDaTurma(matriculas=[mat(1, _dias(30))], tentativas=[], questoes_abertas=ABERTAS)
        funil = montar_funil(dados, 40, AGORA)
        assert set(funil) == {"north_star", "aquisicao", "ativacao", "retencao", "saude", "protecao"}
        assert funil["aquisicao"]["alunos_previstos"] == 40
