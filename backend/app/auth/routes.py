from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_professor
from app.auth.service import (
    authenticate_professor, create_access_token, hash_password, register_professor, verify_password,
)
from app.models.database import get_db
from app.models.orm import Professor
from app.models.schemas import (
    PasswordChange, ProfessorCreate, ProfessorResponse, ProfessorUpdate, TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: ProfessorCreate, db: Session = Depends(get_db)):
    try:
        professor = register_professor(body.email, body.nome, body.senha, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TokenResponse(
        access_token=create_access_token(professor.id),
        professor=_to_response(professor),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: ProfessorCreate, db: Session = Depends(get_db)):
    professor = authenticate_professor(body.email, body.senha, db)
    if not professor:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    return TokenResponse(
        access_token=create_access_token(professor.id),
        professor=_to_response(professor),
    )


@router.get("/me", response_model=ProfessorResponse)
def me(current: Professor = Depends(get_current_professor)):
    return _to_response(current)


@router.put("/me", response_model=ProfessorResponse)
def update_me(
    body: ProfessorUpdate,
    db: Session = Depends(get_db),
    current: Professor = Depends(get_current_professor),
):
    current.nome = body.nome.strip()
    db.commit()
    db.refresh(current)
    return _to_response(current)


@router.put("/me/password", status_code=204)
def change_password(
    body: PasswordChange,
    db: Session = Depends(get_db),
    current: Professor = Depends(get_current_professor),
):
    if not verify_password(body.senha_atual, current.senha_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    current.senha_hash = hash_password(body.senha_nova)
    db.commit()


def _to_response(p: Professor) -> ProfessorResponse:
    return ProfessorResponse(
        id=p.id,
        email=p.email,
        nome=p.nome,
        created_at=p.created_at.isoformat(),
    )
