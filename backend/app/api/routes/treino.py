from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.student_dependencies import get_current_student
from app.models.database import get_db
from app.models.orm import Student
from app.models.schemas import (
    ExercicioDetalhe, ReportarExercicioRequest, TreinoGerarRequest,
    TreinoSubmissaoRequest, TreinoSubmissaoResponse, TrilhaResponse,
)
from app.services.treino_service import (
    TreinoIndisponivel, detalhe, gerar_para_categoria, reportar, treinar, trilha,
)

router = APIRouter(prefix="/aluno/treino", tags=["aluno — treino"])


@router.get("", response_model=TrilhaResponse)
def get_trilha(
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    return trilha(current, db)


@router.post("/gerar", response_model=ExercicioDetalhe, status_code=201)
def post_gerar(
    body: TreinoGerarRequest,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    """Gera um exercício para a categoria pedida, ou para a que o aluno mais erra.

    Devolve 409 quando não há o que gerar agora, com o motivo em texto: teto
    diário atingido, ou ainda sem erro suficiente para montar a trilha."""
    try:
        return gerar_para_categoria(current, body.error_category, db)
    except TreinoIndisponivel as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/{exercicio_id}", response_model=ExercicioDetalhe)
def get_exercicio(
    exercicio_id: int,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    try:
        return detalhe(current, exercicio_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{exercicio_id}/tentativas", response_model=TreinoSubmissaoResponse, status_code=201)
def post_tentativa(
    exercicio_id: int,
    body: TreinoSubmissaoRequest,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    """Sem janela e sem teto de tentativas: é treino."""
    try:
        return treinar(current, exercicio_id, body.code, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{exercicio_id}/reportar")
def post_reportar(
    exercicio_id: int,
    body: ReportarExercicioRequest,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    """O gerado não passa por revisão do professor, então quem sinaliza exercício
    ruim é o aluno. Reportado sai da trilha."""
    try:
        return reportar(current, exercicio_id, body.motivo, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
