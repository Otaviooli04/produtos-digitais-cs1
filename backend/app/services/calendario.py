"""Recortes de tempo usados por mais de um serviço: a semana de um envio e a
situação de uma atividade num instante."""
from datetime import datetime, timedelta

from app.models.orm import Exam


def semana_iso(momento: datetime) -> str:
    """Segunda-feira da semana do momento, em ISO. É o que identifica a semana."""
    dia = momento.date()
    return (dia - timedelta(days=dia.weekday())).isoformat()


def situacao_da_atividade(exam: Exam, agora: datetime | None = None) -> str:
    agora = agora or datetime.utcnow()
    if exam.abre_em and agora < exam.abre_em:
        return "agendada"
    if exam.fecha_em and agora > exam.fecha_em:
        return "encerrada"
    return "aberta"
