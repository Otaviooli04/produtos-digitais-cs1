from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.service import decode_token
from app.models.database import get_db
from app.models.orm import Professor

_bearer = HTTPBearer()


def get_current_professor(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> Professor:
    professor_id = decode_token(credentials.credentials)
    if professor_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado.")
    professor = db.get(Professor, professor_id)
    if professor is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Professor não encontrado.")
    return professor
