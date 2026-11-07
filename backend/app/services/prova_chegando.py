"""Prova chegando (experimento 5): o treino curto que o Início oferece nos três
dias antes de uma prova abrir. Funções puras sobre registros simples, testadas
sem banco. O cartão é calculado na hora, sem tabela própria."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.models.orm import Exam
from app.services.funil_regras import ANTECEDENCIA_DA_PROVA

if TYPE_CHECKING:
    from app.services.inicio_service import AtividadeDoPainel

MAXIMO_DE_ERROS = 3


def prova_na_janela(atividades: list[AtividadeDoPainel], agora: datetime) -> AtividadeDoPainel | None:
    """A prova agendada que abre nos próximos 3 dias e ainda tem o que fazer. Com
    mais de uma, a que abre primeiro, e no empate a de menor id."""
    na_janela = [
        a for a in atividades
        if a.modo == Exam.MODO_PROVA and a.situacao == "agendada" and a.com_o_que_fazer
        and a.abre_em and a.abre_em - ANTECEDENCIA_DA_PROVA <= agora < a.abre_em
    ]
    return min(na_janela, key=lambda a: (a.abre_em, a.exam_id), default=None)
