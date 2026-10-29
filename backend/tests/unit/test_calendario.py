from datetime import datetime

from app.models.orm import Exam
from app.services.calendario import semana_iso, situacao_da_atividade


def test_semana_vai_de_segunda_a_domingo():
    assert semana_iso(datetime(2026, 10, 26, 0, 0)) == "2026-10-26"
    assert semana_iso(datetime(2026, 11, 1, 23, 59)) == "2026-10-26"
    assert semana_iso(datetime(2026, 11, 2, 0, 0)) == "2026-11-02"


def test_situacao_da_atividade():
    agora = datetime(2026, 10, 26, 12, 0)
    assert situacao_da_atividade(Exam(), agora) == "aberta"
    assert situacao_da_atividade(Exam(abre_em=datetime(2026, 10, 27)), agora) == "agendada"
    assert situacao_da_atividade(Exam(fecha_em=datetime(2026, 10, 25)), agora) == "encerrada"
