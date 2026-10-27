"""
Funil de todas as turmas, para a equipe acompanhar a North Star sem criar papel
de administrador. Mostra só números: nenhum nome de aluno sai daqui.

Uso:
    cd backend
    venv/bin/python scripts/funil.py
"""
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.database import SessionLocal
from app.services.funil_service import funil_geral


def _pct(valor: float | None) -> str:
    return "sem dado" if valor is None else f"{valor}%"


def relatorio(db: Session, agora: datetime | None = None) -> str:
    funil = funil_geral(db, agora)
    total = funil["total"]
    ns = total["north_star"]
    semana = total["retencao_ultima_semana"]
    linhas = [
        f"Funil de todas as turmas, gerado em {funil['gerado_em'][:16].replace('T', ' ')} UTC",
        "",
        "North Star, erros corrigidos por semana",
        *(f"  {s['semana']}  {s['erros_corrigidos']}" for s in ns["semanas"]),
        f"  Total desde o início: {ns['total']}",
        "",
        "Total",
        f"  Professores com turma: {total['professores_com_turma']}",
        f"  Turmas com matrícula: {total['turmas_com_matricula']}",
        f"  Matriculados: {total['matriculados']}",
        f"  Ativados: {total['ativados']} ({_pct(total['taxa_ativacao'])})",
        f"  Retenção na semana de {semana['semana']}: {semana['voltaram']} de {semana['base']} "
        f"({_pct(semana['taxa'])})",
        "",
        "Por turma",
    ]
    if not funil["por_turma"]:
        linhas.append("  Nenhuma turma cadastrada.")
    for t in funil["por_turma"]:
        previstos = f" de {t['alunos_previstos']} previstos" if t["alunos_previstos"] else ""
        linhas.append(
            f"  {t['nome']} ({t['professor'] or 'sem professor'}): "
            f"{t['matriculados']} matriculados{previstos}, "
            f"ativação {_pct(t['taxa_ativacao'])}, retenção {_pct(t['taxa_retencao'])}, "
            f"erros corrigidos {t['north_star_semana']} na semana e {t['north_star_total']} no total, "
            f"{t['vermelhos']} em vermelho"
        )
    return "\n".join(linhas)


def main() -> None:
    db = SessionLocal()
    try:
        print(relatorio(db))
    finally:
        db.close()


if __name__ == "__main__":
    main()
