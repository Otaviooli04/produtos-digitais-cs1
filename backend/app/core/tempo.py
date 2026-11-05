from datetime import datetime, timezone


def agora_utc() -> datetime:
    """Agora em UTC e sem fuso, o formato que o banco guarda desde o início.
    Ocupa o lugar do `datetime.utcnow`, que o Python 3.12 marcou como obsoleto."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
