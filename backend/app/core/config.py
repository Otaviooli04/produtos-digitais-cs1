import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
DATABASE_URL: str = os.environ.get("DATABASE_URL", "")

SECRET_KEY: str = os.environ.get(
    "SECRET_KEY",
    "dev-secret-key-troque-em-producao-please-change-me-now",
)
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRE_HOURS: int = 8
