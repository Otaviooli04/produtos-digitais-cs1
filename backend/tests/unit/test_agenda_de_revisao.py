from datetime import date, datetime

from app.services.calendario import dia_local
from app.services.historico_do_aluno import (
    ACERTO, ERRO, LISTA, TRILHA, Envio, agenda_de_revisao, erros_do_aluno,
)

CAT = "Acesso Fora dos Limites: Off-by-One"


def _dia(d, hora=15):
    """15h UTC é meio-dia em Brasília, longe da virada do dia."""
    return datetime(2026, 11, d, hora)


def _erro_na_lista(momento):
    return Envio(origem=LISTA, item_id=1, momento=momento, categoria=CAT, resultado=ERRO)


def _acerto_na_trilha(exercicio, momento, categoria="Correto"):
    return Envio(origem=TRILHA, item_id=exercicio, momento=momento, categoria=categoria,
                 resultado=ACERTO, alvo=CAT, titulo="Soma")


def _erro_na_trilha(exercicio, momento):
    return Envio(origem=TRILHA, item_id=exercicio, momento=momento, categoria=CAT,
                 resultado=ERRO, alvo=CAT, titulo="Soma")


def _agenda(envios, hoje):
    erro = next(e for e in erros_do_aluno(envios) if e.categoria == CAT)
    return agenda_de_revisao(erro, envios, hoje)


def test_dia_local_e_o_dia_de_brasilia():
    assert dia_local(datetime(2026, 11, 17, 1, 0)) == date(2026, 11, 16)
    assert dia_local(datetime(2026, 11, 17, 3, 0)) == date(2026, 11, 17)


def test_primeira_revisao_vence_no_dia_seguinte():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2))]
    no_dia = _agenda(envios, date(2026, 11, 2))
    assert (no_dia.feitas, no_dia.proxima_em, no_dia.dias_ate) == (0, date(2026, 11, 3), 1)
    assert not no_dia.vencida
    assert _agenda(envios, date(2026, 11, 3)).vencida


def test_dia_conta_pelo_horario_de_brasilia():
    """Superado às 22h de Brasília do dia 16, que já é dia 17 em UTC."""
    envios = [_erro_na_lista(datetime(2026, 11, 16, 10)),
              _acerto_na_trilha(10, datetime(2026, 11, 17, 1, 0))]
    agenda = _agenda(envios, date(2026, 11, 17))
    assert agenda.proxima_em == date(2026, 11, 17)
    assert agenda.vencida


def test_acerto_antes_do_vencimento_nao_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(2, hora=17))]
    agenda = _agenda(envios, date(2026, 11, 3))
    assert agenda.feitas == 0
    assert agenda.vencida


def test_acerto_depois_do_vencimento_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(3))]
    agenda = _agenda(envios, date(2026, 11, 3))
    assert (agenda.feitas, agenda.proxima_em, agenda.dias_ate) == (1, date(2026, 11, 9), 6)


def test_tres_revisoes_consolidam():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(3)), _acerto_na_trilha(12, _dia(9)),
              _acerto_na_trilha(13, _dia(24))]
    agenda = _agenda(envios, date(2026, 11, 30))
    assert agenda.feitas == 3
    assert agenda.consolidado
    assert agenda.proxima_em is None and agenda.dias_ate is None
    assert not agenda.vencida


def test_refazer_exercicio_resolvido_antes_do_vencimento_nao_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(2, hora=17)), _acerto_na_trilha(11, _dia(3))]
    assert _agenda(envios, date(2026, 11, 3)).feitas == 0


def test_refazer_o_exercicio_que_superou_nao_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(10, _dia(3))]
    assert _agenda(envios, date(2026, 11, 3)).feitas == 0


def test_acerto_com_a_propria_categoria_nao_conta():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(3), categoria=CAT)]
    assert _agenda(envios, date(2026, 11, 3)).feitas == 0


def test_revisao_que_repete_o_erro_volta_a_ativo():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _erro_na_trilha(11, _dia(3))]
    assert _agenda(envios, date(2026, 11, 3)) is None


def test_superado_de_novo_recomeca_a_agenda():
    envios = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
              _acerto_na_trilha(11, _dia(3)), _erro_na_lista(_dia(4)),
              _acerto_na_trilha(12, _dia(5))]
    agenda = _agenda(envios, date(2026, 11, 5))
    assert (agenda.feitas, agenda.proxima_em) == (0, date(2026, 11, 6))


def test_sem_a_tentativa_reportada_a_revisao_some():
    """Tentativa de exercício reportado não entra no histórico (`ler_historico`)."""
    com = [_erro_na_lista(_dia(1)), _acerto_na_trilha(10, _dia(2)),
           _acerto_na_trilha(11, _dia(3))]
    sem = com[:2]
    assert _agenda(com, date(2026, 11, 3)).feitas == 1
    assert _agenda(sem, date(2026, 11, 3)).feitas == 0


def test_erro_ativo_nao_tem_agenda():
    assert _agenda([_erro_na_lista(_dia(1))], date(2026, 11, 3)) is None
