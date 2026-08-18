from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.student_dependencies import get_current_student
from app.models.database import get_db
from app.models.orm import Student
from app.models.schemas import (
    AlunoSubmissaoRequest, AlunoSubmissaoResponse, AtividadeDetalhe, AtividadeResumo,
    ErrosRecorrentesResponse, HistoricoQuestaoResponse, ProgressoResponse,
)
from app.services.student_activity_service import (
    AtividadeIndisponivel, detalhe_atividade, erros_recorrentes, historico_questao,
    listar_atividades, progresso, submeter,
)

router = APIRouter(prefix="/aluno", tags=["aluno — atividades"])


@router.get("/atividades", response_model=list[AtividadeResumo])
def get_atividades(
    turma_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    try:
        return listar_atividades(current, db, turma_id=turma_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/atividades/{exam_id}", response_model=AtividadeDetalhe)
def get_atividade(
    exam_id: int,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    try:
        return detalhe_atividade(current, exam_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/atividades/{exam_id}/questoes/{question_number}/submissoes",
    response_model=AlunoSubmissaoResponse,
    status_code=201,
)
def post_submissao(
    exam_id: int,
    question_number: str,
    body: AlunoSubmissaoRequest,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    if not body.code.strip():
        raise HTTPException(status_code=400, detail="Envie o código antes de submeter.")
    try:
        return submeter(current, exam_id, question_number, body.code, db)
    except AtividadeIndisponivel as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get(
    "/atividades/{exam_id}/questoes/{question_number}/tentativas",
    response_model=HistoricoQuestaoResponse,
)
def get_tentativas(
    exam_id: int,
    question_number: str,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    try:
        return historico_questao(current, exam_id, question_number, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/progresso", response_model=ProgressoResponse)
def get_progresso(
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    return progresso(current, db)


@router.get("/erros-recorrentes", response_model=ErrosRecorrentesResponse)
def get_erros_recorrentes(
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    return erros_recorrentes(current, db)
