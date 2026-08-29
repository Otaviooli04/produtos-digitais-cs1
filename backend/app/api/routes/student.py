from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.service import hash_password, verify_password
from app.auth.student_dependencies import get_current_student
from app.auth.student_service import (
    authenticate_student, create_student_token, entrar_na_turma, register_student,
)
from app.models.database import get_db
from app.models.orm import Student
from app.models.schemas import (
    PasswordChange, StudentCreate, StudentLogin, StudentResponse, StudentTokenResponse,
    StudentUpdate, TurmaDoAlunoResponse, TurmaEntrarRequest,
)

router = APIRouter(prefix="/aluno", tags=["aluno"])


@router.post("/register", response_model=StudentTokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: StudentCreate, db: Session = Depends(get_db)):
    try:
        student = register_student(body.email, body.nome, body.matricula, body.senha, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StudentTokenResponse(
        access_token=create_student_token(student.id),
        aluno=_to_response(student),
    )


@router.post("/login", response_model=StudentTokenResponse)
def login(body: StudentLogin, db: Session = Depends(get_db)):
    student = authenticate_student(body.email, body.senha, db)
    if not student:
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")
    return StudentTokenResponse(
        access_token=create_student_token(student.id),
        aluno=_to_response(student),
    )


@router.get("/me", response_model=StudentResponse)
def me(current: Student = Depends(get_current_student)):
    return _to_response(current)


@router.put("/me", response_model=StudentResponse)
def update_me(
    body: StudentUpdate,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    current.nome = body.nome.strip()
    current.matricula = body.matricula.strip() or None
    db.commit()
    db.refresh(current)
    return _to_response(current)


@router.put("/me/password", status_code=204)
def change_password(
    body: PasswordChange,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    if not verify_password(body.senha_atual, current.senha_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    current.senha_hash = hash_password(body.senha_nova)
    db.commit()


@router.post("/turmas/entrar", response_model=TurmaDoAlunoResponse)
def entrar(
    body: TurmaEntrarRequest,
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    try:
        turma = entrar_na_turma(current, body.codigo_acesso, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _turma_to_response(turma)


@router.get("/turmas", response_model=list[TurmaDoAlunoResponse])
def minhas_turmas(
    db: Session = Depends(get_db),
    current: Student = Depends(get_current_student),
):
    return [_turma_to_response(e.turma) for e in current.enrollments]


def _to_response(s: Student) -> StudentResponse:
    return StudentResponse(
        id=s.id,
        email=s.email,
        nome=s.nome,
        matricula=s.matricula,
        created_at=s.created_at.isoformat(),
    )


def _turma_to_response(turma) -> TurmaDoAlunoResponse:
    return TurmaDoAlunoResponse(
        id=turma.id,
        nome=turma.nome,
        codigo=turma.codigo,
        professor_nome=turma.professor.nome if turma.professor else None,
        exam_count=len(turma.exams),
    )
