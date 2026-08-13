from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.student_service import decode_student_token
from app.models.database import get_db
from app.models.orm import Student

_bearer = HTTPBearer()


def get_current_student(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Student:
    student_id = decode_student_token(credentials.credentials)
    if student_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado.")
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Aluno não encontrado.")
    return student
