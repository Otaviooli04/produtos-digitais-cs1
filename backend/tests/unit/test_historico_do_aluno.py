"""Regras do histórico do aluno sobre registros montados à mão, sem banco."""
from datetime import date, datetime, timedelta

from app.services.historico_do_aluno import (
    ACERTO, ERRO, FALHA, LISTA, TRILHA, Envio, Tendencia, dias_seguidos, erros_do_aluno,
    evolucao, resolucoes, resultado_da_lista, resultado_da_trilha, rotulos, superados,
    tendencias,
)

# Quarta-feira, 28/10/2026, ao meio-dia.
T0 = datetime(2026, 10, 28, 12, 0)
OFF = "Acesso Fora dos Limites: Off-by-One"
LACO = "Laço Infinito"


def lista(minutos, resultado=ERRO, categoria=OFF, item=1, o_que_fazer="faça assim"):
    return Envio(origem=LISTA, item_id=item, momento=T0 + timedelta(minutes=minutos),
                 categoria="Correto" if resultado == ACERTO else categoria,
                 resultado=resultado, o_que_fazer=o_que_fazer)


def trilha(minutos, resultado=ACERTO, alvo=OFF, categoria=None, item=100,
           titulo="Soma dos pares", o_que_fazer=""):
    if categoria is None:
        categoria = "Correto" if resultado == ACERTO else alvo
    return Envio(origem=TRILHA, item_id=item, momento=T0 + timedelta(minutes=minutos),
                 categoria=categoria, resultado=resultado, o_que_fazer=o_que_fazer,
                 alvo=alvo, titulo=titulo)


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


class TestErros:
    def test_acerto_no_treino_do_mesmo_erro_supera(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10)])
        assert not erro.ativo
        assert erro.superado_em == T0 + timedelta(minutes=10)

    def test_acerto_antes_da_ultima_ocorrencia_nao_supera(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10), lista(20)])
        assert erro.ativo
        assert erro.superado_em is None

    def test_erro_que_volta_precisa_de_novo_acerto(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10), lista(20), trilha(30, item=101)])
        assert erro.superado_em == T0 + timedelta(minutes=30)

    def test_acerto_em_exercicio_de_outro_erro_nao_supera(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10, alvo=LACO)])
        assert erro.ativo

    def test_acerto_que_repete_o_erro_do_exercicio_nao_supera(self):
        """Violação de estrutura e aviso saem antes dos testes: o exercício
        passa, mas o erro para o qual ele foi feito continua ali."""
        estrutura = "Violação de Estrutura"
        (erro,) = erros_do_aluno([
            lista(0, categoria=estrutura),
            trilha(10, alvo=estrutura, categoria=estrutura),
        ])
        assert erro.ativo
        assert erro.superado_em is None

    def test_superado_em_e_o_primeiro_acerto_depois_da_ultima_ocorrencia(self):
        (erro,) = erros_do_aluno([lista(0), trilha(10), trilha(20)])
        assert erro.superado_em == T0 + timedelta(minutes=10)

    def test_erro_cometido_no_treino_vira_erro_ativo(self):
        erros = erros_do_aluno([lista(0), trilha(10, resultado=ERRO, categoria=LACO)])
        laco = next(e for e in erros if e.categoria == LACO)
        assert laco.ativo
        assert laco.total == 1
        assert laco.no_treino == 1

    def test_falha_tecnica_nao_vira_erro(self):
        assert erros_do_aluno([lista(0, FALHA, categoria="Erro Desconhecido")]) == []

    def test_contas_do_erro(self):
        (erro,) = erros_do_aluno([
            lista(0, o_que_fazer="primeiro"),
            trilha(10, resultado=ERRO),
            lista(20, item=2, o_que_fazer="último"),
        ])
        assert erro.total == 3
        assert erro.no_treino == 1
        assert erro.o_que_fazer == "último"
        assert erro.ultima_ocorrencia == T0 + timedelta(minutes=20)

    def test_ordem_ativos_pelo_total_e_nome_superados_do_mais_recente(self):
        envios = [
            lista(0, categoria="B"), lista(1, categoria="B"),
            lista(2, categoria="A"), lista(3, categoria="A"),
            lista(4, categoria="C"), lista(5, categoria="C"), lista(6, categoria="C"),
            lista(7, categoria="D"), trilha(8, alvo="D"),
            lista(9, categoria="E"), trilha(10, alvo="E", item=101),
        ]
        assert [e.categoria for e in erros_do_aluno(envios)] == ["C", "A", "B", "E", "D"]

    def test_superados_no_formato_da_tela(self):
        erros = erros_do_aluno([lista(0), lista(1), trilha(10), lista(20, categoria=LACO)])
        assert superados(erros) == [
            {"error_category": OFF, "total": 2, "superado_em": "2026-10-28T12:10:00"},
        ]

    def test_rotulos_do_mais_recente_sem_repetir_no_maximo_cinco(self):
        envios = [lista(i, item=i) for i in range(1, 7)] + [
            lista(7, item=1), trilha(8, resultado=ERRO), lista(9, item=99),
        ]
        (erro,) = erros_do_aluno(envios)
        rotulo_da_questao = {i: f"Lista 1 · Q{i}" for i in range(1, 7)}
        assert rotulos(erro, rotulo_da_questao) == [
            "Trilha · Soma dos pares", "Lista 1 · Q1", "Lista 1 · Q6", "Lista 1 · Q5",
            "Lista 1 · Q4",
        ]


class TestTendencia:
    def test_erro_que_parou_esta_melhorando_e_o_novo_piorando(self):
        envios = [lista(i, categoria=LACO) for i in range(4)] + [
            lista(10 + i, item=2) for i in range(10)
        ]
        t = tendencias(envios)
        assert t[LACO] == Tendencia(recentes=0, anteriores=4, sentido="melhorando")
        assert t[OFF] == Tendencia(recentes=10, anteriores=0, sentido="piorando")

    def test_sem_tentativa_fora_da_janela_e_estavel(self):
        t = tendencias([lista(0), lista(1, ACERTO, item=2)])
        assert t[OFF] == Tendencia(recentes=1, anteriores=0, sentido="estavel")

    def test_mesma_taxa_dentro_e_fora_da_janela_e_estavel(self):
        envios = [lista(i) if i % 2 == 0 else lista(i, ACERTO, item=2) for i in range(20)]
        t = tendencias(envios)
        assert t[OFF] == Tendencia(recentes=5, anteriores=5, sentido="estavel")

    def test_falha_tecnica_nao_ocupa_a_janela(self):
        antigos = [lista(i, categoria=LACO) for i in range(10)]
        falhas = [lista(20 + i, FALHA, categoria="Erro Desconhecido") for i in range(10)]
        t = tendencias(antigos + falhas)
        assert t[LACO] == Tendencia(recentes=10, anteriores=0, sentido="estavel")
        assert "Erro Desconhecido" not in t


HOJE = date(2026, 10, 28)


def no_dia(dia):
    return Envio(origem=LISTA, item_id=1, momento=datetime(2026, 10, dia, 10, 0),
                 categoria=OFF, resultado=ERRO)


class TestResolucoes:
    def test_conta_so_as_tentativas_validas_ate_o_primeiro_acerto(self):
        envios = [
            lista(0), lista(1, FALHA, categoria="Erro Desconhecido"),
            lista(2, ACERTO), lista(3), lista(4, ACERTO),
        ]
        (r,) = resolucoes(envios)
        assert r.item == (LISTA, 1)
        assert r.tentativas == 2
        assert r.momento == T0 + timedelta(minutes=2)

    def test_falha_antes_do_acerto_ainda_e_acerto_de_primeira(self):
        (r,) = resolucoes([lista(0, FALHA, categoria="Erro Desconhecido"), lista(1, ACERTO)])
        assert r.tentativas == 1

    def test_item_sem_acerto_nao_esta_resolvido(self):
        assert resolucoes([lista(0), trilha(1, resultado=ERRO)]) == []

    def test_questao_e_exercicio_com_o_mesmo_id_sao_itens_diferentes(self):
        rs = resolucoes([lista(0, ACERTO, item=5), trilha(1, item=5)])
        assert sorted(r.item for r in rs) == [(LISTA, 5), (TRILHA, 5)]


class TestDiasSeguidos:
    def test_sequencia_terminando_hoje(self):
        assert dias_seguidos([no_dia(26), no_dia(27), no_dia(28)], HOJE) == 3

    def test_quem_enviou_ontem_mantem_a_sequencia(self):
        assert dias_seguidos([no_dia(26), no_dia(27)], HOJE) == 2

    def test_buraco_zera(self):
        assert dias_seguidos([no_dia(25)], HOJE) == 0
        assert dias_seguidos([], HOJE) == 0


class TestEvolucao:
    def test_tentativas_e_primeiros_acertos_por_semana(self):
        envios = [
            Envio(origem=LISTA, item_id=1, momento=datetime(2026, 10, 14, 10),
                  categoria=OFF, resultado=ERRO),
            Envio(origem=TRILHA, item_id=100, momento=datetime(2026, 10, 27, 10),
                  categoria="Correto", resultado=ACERTO, alvo=OFF),
            Envio(origem=LISTA, item_id=1, momento=datetime(2026, 10, 28, 10),
                  categoria="Correto", resultado=ACERTO),
        ]
        assert evolucao(envios, resolucoes(envios)) == [
            {"periodo": "2026-10-12", "tentativas": 1, "resolvidas": 0},
            {"periodo": "2026-10-26", "tentativas": 2, "resolvidas": 2},
        ]
