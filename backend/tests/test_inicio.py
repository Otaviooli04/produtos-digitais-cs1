"""Início do aluno: o cartão de continuar, a próxima atividade, os prazos e o
painel.

As regras são funções puras, testadas com listas montadas à mão. O painel e as
rotas são testados no banco."""
from datetime import datetime, timedelta

from app.services.historico_do_aluno import ACERTO, ERRO, FALHA, LISTA, TRILHA, Envio
from app.services.inicio_service import (
    AtividadeDoPainel, ItemDisponivel, escolher_continuar, prazos_proximos, proxima_atividade,
)

AGORA = datetime(2026, 11, 4, 12, 0)


def _envio(origem, item_id, minuto, resultado, categoria="Saída Incorreta"):
    return Envio(origem=origem, item_id=item_id, momento=AGORA + timedelta(minutes=minuto),
                 categoria=categoria, resultado=resultado)


def _questao(item_id, numero="1"):
    return ItemDisponivel(origem=LISTA, item_id=item_id, titulo=f"Questão {numero} · Lista 3",
                          turma_nome="Turma A", exam_id=10, question_number=numero)


def _exercicio(item_id, titulo="Soma dos pares"):
    return ItemDisponivel(origem=TRILHA, item_id=item_id, titulo=titulo, exercicio_id=item_id)


def _disponiveis(*itens):
    return {(i.origem, i.item_id): i for i in itens}


def _atividade(exam_id, situacao="aberta", fecha_em=None, abre_em=None, criada_em=AGORA,
               com_o_que_fazer=True):
    return AtividadeDoPainel(
        exam_id=exam_id, titulo=f"Lista {exam_id}", turma_nome="Turma A", modo="prova",
        situacao=situacao, abre_em=abre_em, fecha_em=fecha_em, criada_em=criada_em,
        com_o_que_fazer=com_o_que_fazer)


class TestContinuar:
    def test_pega_o_item_mais_recente_sem_acerto(self):
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(LISTA, 2, 1, ERRO)]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1), _questao(2, "2")), None)
        assert cartao == {
            "origem": "lista", "situacao": "em_andamento", "titulo": "Questão 2 · Lista 3",
            "turma_nome": "Turma A", "tentativas": 1, "ultimo_erro": "Saída Incorreta",
            "exam_id": 10, "question_number": "2", "exercicio_id": None,
        }

    def test_pula_o_resolvido_mesmo_sendo_o_mais_recente(self):
        # A questão 2 tem erro e depois acerto: resolvida, mesmo sendo a última mexida.
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(LISTA, 2, 1, ERRO),
                  _envio(LISTA, 2, 2, ACERTO, "Correto")]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1), _questao(2, "2")), None)
        assert cartao["question_number"] == "1"
        assert cartao["tentativas"] == 1

    def test_pula_o_que_nao_aceita_mais_envio(self):
        # Atividade encerrada ou tentativas esgotadas: o item fica fora dos disponíveis.
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(LISTA, 2, 1, ERRO)]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1)), None)
        assert cartao["question_number"] == "1"

    def test_pula_o_exercicio_resolvido(self):
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(TRILHA, 7, 1, ERRO),
                  _envio(TRILHA, 7, 2, ACERTO, "Correto")]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1), _exercicio(7)), None)
        assert cartao["origem"] == "lista"

    def test_mistura_lista_e_trilha_pela_ordem_do_tempo(self):
        # O exercício 7 teve envio antes e depois da questão 1: ele é o mais recente.
        envios = [_envio(TRILHA, 7, 0, ERRO, "Tudo no Main"), _envio(LISTA, 1, 1, ERRO),
                  _envio(TRILHA, 7, 2, ERRO, "Tudo no Main")]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1), _exercicio(7)), None)
        assert cartao == {
            "origem": "trilha", "situacao": "em_andamento", "titulo": "Soma dos pares",
            "turma_nome": "", "tentativas": 2, "ultimo_erro": "Tudo no Main",
            "exam_id": None, "question_number": None, "exercicio_id": 7,
        }

    def test_ultimo_erro_vazio_quando_foi_falha_tecnica(self):
        envios = [_envio(LISTA, 1, 0, ERRO), _envio(LISTA, 1, 1, FALHA, "Erro Desconhecido")]
        cartao = escolher_continuar(envios, _disponiveis(_questao(1)), None)
        assert cartao["ultimo_erro"] == ""
        assert cartao["tentativas"] == 2

    def test_sem_item_em_andamento_devolve_a_proxima(self):
        proxima = {"situacao": "proxima", "exam_id": 20}
        envios = [_envio(LISTA, 1, 0, ACERTO, "Correto")]
        assert escolher_continuar(envios, _disponiveis(_questao(1)), proxima) is proxima

    def test_sem_nada_devolve_vazio(self):
        assert escolher_continuar([], {}, None) is None


class TestPrazos:
    def test_janela_de_fechamento_de_7_dias(self):
        atividades = [
            _atividade(1, fecha_em=AGORA + timedelta(days=7)),
            _atividade(2, fecha_em=AGORA + timedelta(days=8)),
            _atividade(3, situacao="encerrada", fecha_em=AGORA - timedelta(hours=1)),
        ]
        assert prazos_proximos(atividades, AGORA) == [{
            "exam_id": 1, "titulo": "Lista 1", "turma_nome": "Turma A", "modo": "prova",
            "tipo": "fecha", "quando": (AGORA + timedelta(days=7)).isoformat(),
        }]

    def test_janela_de_abertura_de_3_dias(self):
        atividades = [
            _atividade(1, situacao="agendada", abre_em=AGORA + timedelta(days=3)),
            _atividade(2, situacao="agendada", abre_em=AGORA + timedelta(days=4)),
        ]
        prazos = prazos_proximos(atividades, AGORA)
        assert [(p["exam_id"], p["tipo"]) for p in prazos] == [(1, "abre")]

    def test_sem_o_que_fazer_fica_de_fora(self):
        atividades = [_atividade(1, fecha_em=AGORA + timedelta(days=2), com_o_que_fazer=False)]
        assert prazos_proximos(atividades, AGORA) == []

    def test_ordem_pela_data_e_uma_vez_so(self):
        # A 2 ainda não abriu: entra só pela abertura (1 dia), não pelo fechamento.
        atividades = [
            _atividade(1, fecha_em=AGORA + timedelta(days=5)),
            _atividade(2, situacao="agendada", abre_em=AGORA + timedelta(days=1),
                       fecha_em=AGORA + timedelta(days=6)),
            _atividade(3, fecha_em=AGORA + timedelta(days=2)),
        ]
        prazos = prazos_proximos(atividades, AGORA)
        assert [(p["exam_id"], p["tipo"]) for p in prazos] == [
            (2, "abre"), (3, "fecha"), (1, "fecha")]


class TestProximaAtividade:
    def test_a_que_fecha_primeiro_e_depois_as_sem_prazo_da_mais_nova(self):
        a1 = _atividade(1, fecha_em=AGORA + timedelta(days=5))
        a2 = _atividade(2, fecha_em=AGORA + timedelta(days=2))
        a3 = _atividade(3, criada_em=AGORA - timedelta(days=1))
        a4 = _atividade(4, criada_em=AGORA)
        assert proxima_atividade([a1, a2, a3, a4]) == {
            "origem": "lista", "situacao": "proxima", "titulo": "Lista 2",
            "turma_nome": "Turma A", "tentativas": 0, "ultimo_erro": "", "exam_id": 2,
            "question_number": None, "exercicio_id": None,
        }
        assert proxima_atividade([a3, a4])["exam_id"] == 4

    def test_ignora_a_agendada_e_a_sem_o_que_fazer(self):
        atividades = [_atividade(1, situacao="agendada", abre_em=AGORA + timedelta(days=1)),
                      _atividade(2, com_o_que_fazer=False)]
        assert proxima_atividade(atividades) is None
