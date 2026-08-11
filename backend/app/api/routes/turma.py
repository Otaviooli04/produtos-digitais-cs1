from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_professor
from app.models.database import get_db
from app.models.orm import Professor
from app.models.orm import Turma
from app.models.schemas import (
    TurmaAnalyticsResponse, TurmaCreate, TurmaDetailResponse, TurmaResponse, TurmaUpdate,
)
from app.services.turma_service import (
    create_turma, delete_turma, get_turma_analytics, get_turma_detail, list_turmas, update_turma,
)

router = APIRouter(prefix="/turmas", tags=["turmas"])


def _get_turma_or_404(turma_id: int, db: Session, professor_id: int) -> Turma:
    turma = db.query(Turma).filter(
        Turma.id == turma_id, Turma.professor_id == professor_id,
    ).first()
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return turma


@router.get("", response_model=list[TurmaResponse])
def get_turmas(
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    return list_turmas(db, professor_id=professor.id)


@router.post("", response_model=TurmaDetailResponse)
def post_turma(
    body: TurmaCreate,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    turma = create_turma(body.nome, body.codigo, db, professor_id=professor.id)
    return get_turma_detail(turma.id, db)


@router.get("/{turma_id}", response_model=TurmaDetailResponse)
def get_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    detail = get_turma_detail(turma_id, db, professor_id=professor.id)
    if not detail:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return detail


@router.put("/{turma_id}", response_model=TurmaDetailResponse)
def put_turma(
    turma_id: int,
    body: TurmaUpdate,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    turma = _get_turma_or_404(turma_id, db, professor.id)
    update_turma(turma, body.nome, body.codigo, db)
    return get_turma_detail(turma.id, db)


@router.delete("/{turma_id}", status_code=204)
def remove_turma(
    turma_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    turma = _get_turma_or_404(turma_id, db, professor.id)
    delete_turma(turma, db)


@router.get("/{turma_id}/analytics", response_model=TurmaAnalyticsResponse)
def get_analytics(
    turma_id: int,
    db: Session = Depends(get_db),
    professor: Professor = Depends(get_current_professor),
):
    data = get_turma_analytics(turma_id, db, professor_id=professor.id)
    if not data:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return data
