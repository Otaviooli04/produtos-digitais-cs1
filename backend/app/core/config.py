import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

# Sem valor padrão de propósito: com uma chave escrita no código, qualquer um
# que leia o repositório forja token de professor.
SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY não definido. Configure a variável no backend/.env.")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_HOURS: int = 8
