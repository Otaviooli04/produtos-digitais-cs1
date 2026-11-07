"""Prova chegando (experimento 5): qual prova entra no cartão e quais erros ele mostra."""
from datetime import datetime, timedelta

from app.services.inicio_service import AtividadeDoPainel
from app.services.prova_chegando import prova_na_janela

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
