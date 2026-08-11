"""Execução de tarefas longas em segundo plano com rastreio de progresso.

As rotas criam um `ProcessingJob`, disparam a função pesada numa thread daemon
com sessão de banco própria e retornam imediatamente. O frontend acompanha o
progresso via polling (`GET /jobs/...`), deixando o usuário livre no sistema.

Threads são adequadas aqui: o trabalho é dominado por I/O (chamada ao Gemini,
`docker run` por test case via subprocess) e o PostgreSQL aceita uma sessão por
thread sem problemas.
"""
import threading

from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models.orm import ProcessingJob


def create_job(db: Session, kind: str, *, exam_id=None, professor_id=None,
               total: int = 0, stage: str = "") -> ProcessingJob:
    job = ProcessingJob(
        kind=kind, exam_id=exam_id, professor_id=professor_id,
        total=total, stage=stage, status="pending", processed=0, result={},
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def update_job(db: Session, job_id: int, **fields) -> None:
    db.query(ProcessingJob).filter(ProcessingJob.id == job_id).update(fields)
    db.commit()


def run_in_background(job_id: int, target) -> None:
    """Executa `target(db, job_id)` numa thread daemon com sessão própria.

    Marca o job como 'running' antes e captura exceções como status 'error',
    para que uma falha (ex.: GEMINI_API_KEY ausente, Docker fora do ar) apareça
    no acompanhamento em vez de derrubar silenciosamente a tarefa.
    """
    def _worker():
        db = SessionLocal()
        try:
            update_job(db, job_id, status="running")
            target(db, job_id)
        except Exception as e:  # noqa: BLE001 — o erro é reportado ao usuário
            try:
                update_job(db, job_id, status="error", message=str(e))
            except Exception:
                pass
        finally:
            db.close()

    threading.Thread(target=_worker, daemon=True).start()
