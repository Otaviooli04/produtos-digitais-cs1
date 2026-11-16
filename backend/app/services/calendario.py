"""Recortes de tempo usados por mais de um serviço: a semana de um envio e a
situação de uma atividade num instante."""
from datetime import date, datetime, timedelta
from app.core.tempo import agora_utc

from app.models.orm import Exam


def semana_iso(momento: datetime) -> str:
    """Segunda-feira da semana do momento, em ISO. É o que identifica a semana."""
    dia = momento.date()
    return (dia - timedelta(days=dia.weekday())).isoformat()


def dia_local(momento: datetime) -> date:
    """A data em Brasília (UTC−3, sem horário de verão desde 2019) de um momento
    em UTC sem fuso, que é como o banco guarda. É o "amanhã" que o aluno entende."""
    return (momento - timedelta(hours=3)).date()


def situacao_da_atividade(exam: Exam, agora: datetime | None = None) -> str:
    agora = agora or agora_utc()
    if exam.abre_em and agora < exam.abre_em:
        return "agendada"
    if exam.fecha_em and agora > exam.fecha_em:
        return "encerrada"
    return "aberta"
