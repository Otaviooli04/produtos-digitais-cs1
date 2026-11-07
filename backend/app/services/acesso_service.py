"""Registro da abertura do app do aluno (RF14), no máximo um por janela."""
from datetime import datetime, timedelta
from app.core.tempo import agora_utc

from sqlalchemy.orm import Session

from app.models.orm import Acesso

# Só origens conhecidas entram no banco, para não guardar texto livre da URL.
# Os tipos de aviso chegam na fase 4.
VIAS_ACEITAS = {"convite", "prova_chegando"}
JANELA_DO_ACESSO = timedelta(minutes=30)


def normalizar_via(via: str | None) -> str | None:
    via = (via or "").strip().lower()
    return via if via in VIAS_ACEITAS else None


def registrar_acesso(student_id: int, via: str | None, db: Session,
                     agora: datetime | None = None) -> bool:
    """Reabrir o app sem origem perto de qualquer acesso não conta, para quem
    entrou pelo convite e voltou à aba não ganhar uma abertura sem aviso. Com
    origem, só não conta se a mesma origem já entrou na janela."""
    agora = agora or agora_utc()
    via = normalizar_via(via)
    recentes = {
        v for (v,) in db.query(Acesso.via).filter(
            Acesso.student_id == student_id,
            Acesso.momento > agora - JANELA_DO_ACESSO,
        ).all()
    }
    if recentes and (via is None or via in recentes):
        return False
    db.add(Acesso(student_id=student_id, momento=agora, via=via))
    db.commit()
    return True
