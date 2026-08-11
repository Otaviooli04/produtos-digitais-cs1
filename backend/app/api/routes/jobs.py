from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_professor
from app.models.database import get_db
from app.models.orm import Professor, ProcessingJob
from app.models.schemas import JobResponse

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_response(job: ProcessingJob) -> JobResponse:
    return JobResponse(
        id=job.id,
        kind=job.kind,
        status=job.status,
        stage=job.stage or "",
        total=job.total or 0,
        processed=job.processed or 0,
        message=job.message or "",
        result=job.result or None,
        exam_id=job.exam_id,
        created_at=job.created_at.isoformat() if job.created_at else "",
    )


@router.get("/active", response_model=list[JobResponse])
def list_active_jobs(
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    """Jobs ainda em andamento do professor (alimenta o indicador global de progresso)."""
    jobs = (
        db.query(ProcessingJob)
        .filter(
            ProcessingJob.professor_id == professor.id,
            ProcessingJob.status.in_(["pending", "running"]),
        )
        .order_by(ProcessingJob.created_at.desc())
        .all()
    )
    return [_to_response(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    job = db.query(ProcessingJob).filter(
        ProcessingJob.id == job_id,
        ProcessingJob.professor_id == professor.id,
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return _to_response(job)
