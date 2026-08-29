from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.auth.service import hash_password, verify_password
from app.core.config import JWT_ALGORITHM, JWT_EXPIRE_HOURS, SECRET_KEY
from app.models.orm import Enrollment, Exam, Question, Student, Submission, Turma

# O token do aluno carrega um papel próprio para que um token de professor nunca
# seja aceito onde se espera um aluno, e vice-versa.
STUDENT_ROLE = "student"


def create_student_token(student_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(student_id), "role": STUDENT_ROLE, "exp": expire},
        SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_student_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("role") != STUDENT_ROLE:
        return None
    try:
        return int(payload["sub"])
    except (KeyError, ValueError):
        return None


def register_student(email: str, nome: str, matricula: str, senha: str, db: Session) -> Student:
    email = email.lower().strip()
    if db.query(Student).filter(Student.email == email).first():
        raise ValueError("E-mail já cadastrado.")
    student = Student(
        email=email,
        nome=nome.strip(),
        matricula=(matricula or "").strip() or None,
        senha_hash=hash_password(senha),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    vincular_submissoes_anteriores(student, db)
    return student


def authenticate_student(email: str, senha: str, db: Session) -> Student | None:
    student = db.query(Student).filter(Student.email == email.lower().strip()).first()
    if not student or not verify_password(senha, student.senha_hash):
        return None
    return student


def entrar_na_turma(student: Student, codigo_acesso: str, db: Session) -> Turma:
    """Vincula o aluno à turma pelo código de acesso. Idempotente: entrar de novo
    na mesma turma devolve o vínculo existente em vez de duplicar."""
    codigo = (codigo_acesso or "").strip().upper()
    turma = db.query(Turma).filter(Turma.codigo_acesso == codigo).first()
    if not turma:
        raise ValueError("Código de turma inválido.")

    ja_vinculado = db.query(Enrollment).filter(
        Enrollment.student_id == student.id,
        Enrollment.turma_id == turma.id,
    ).first()
    if not ja_vinculado:
        db.add(Enrollment(student_id=student.id, turma_id=turma.id))
        db.commit()
        vincular_submissoes_anteriores(student, db)
    return turma


def vincular_submissoes_anteriores(student: Student, db: Session) -> int:
    """Religa ao aluno as submissões feitas antes da conta existir, casando pela
    matrícula dentro das turmas em que ele está. Sem matrícula não há como casar
    com segurança, então nada é feito."""
    if not student.matricula:
        return 0

    turma_ids = [e.turma_id for e in student.enrollments]
    if not turma_ids:
        return 0

    orfas = (
        db.query(Submission)
        .join(Submission.question)
        .join(Question.exam)
        .filter(
            Submission.student_id.is_(None),
            Submission.matricula == student.matricula,
            Exam.turma_id.in_(turma_ids),
        )
        .all()
    )
    for sub in orfas:
        sub.student_id = student.id
    if orfas:
        db.commit()
    return len(orfas)
