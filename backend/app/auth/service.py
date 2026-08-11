from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import JWT_ALGORITHM, JWT_EXPIRE_HOURS, SECRET_KEY
from app.models.orm import Professor

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def create_access_token(professor_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(professor_id), "exp": expire},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        return None


def register_professor(email: str, nome: str, senha: str, db: Session) -> Professor:
    if db.query(Professor).filter(Professor.email == email.lower()).first():
        raise ValueError("E-mail já cadastrado.")
    professor = Professor(
        email=email.lower().strip(),
        nome=nome.strip(),
        senha_hash=hash_password(senha),
    )
    db.add(professor)
    db.commit()
    db.refresh(professor)
    return professor


def authenticate_professor(email: str, senha: str, db: Session) -> Professor | None:
    professor = db.query(Professor).filter(Professor.email == email.lower()).first()
    if not professor or not verify_password(senha, professor.senha_hash):
        return None
    return professor
