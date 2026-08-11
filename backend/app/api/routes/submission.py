from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.auth.dependencies import get_current_professor
from app.models.database import get_db
from app.models.orm import Professor, Submission
from app.models.schemas import CodeSubmissionRequest, CodeSubmissionResponse
from app.services.submission_service import (
    delete_submission, evaluate_submission, reevaluate_submission,
)

router = APIRouter(prefix="/submission", tags=["submission"])


def _get_submission_or_404(submission_id: int, db: Session, professor_id: int) -> Submission:
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    # ownership: submissão → questão → prova → turma → professor
    if (not sub or sub.question is None or sub.question.exam is None
            or sub.question.exam.turma is None
            or sub.question.exam.turma.professor_id != professor_id):
        raise HTTPException(status_code=404, detail="Submissão não encontrada.")
    return sub


@router.post("/evaluate", response_model=CodeSubmissionResponse)
async def submit_answer(body: CodeSubmissionRequest, db: Session = Depends(get_db)):
    try:
        return evaluate_submission(body.exam_id, body.question_number, body.code, db, matricula=body.matricula, dry_run=body.dry_run)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/{submission_id}/reevaluate", response_model=CodeSubmissionResponse)
def reevaluate(
    submission_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    sub = _get_submission_or_404(submission_id, db, professor.id)
    try:
        return reevaluate_submission(sub, db)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/{submission_id}", status_code=204)
def remove_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    sub = _get_submission_or_404(submission_id, db, professor.id)
    delete_submission(sub, db)
