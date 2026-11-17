"""
Refaz os grupos de dificuldade de todas as questões.

Os grupos olham o envio atual de cada aluno. As questões agrupadas antes dessa
regra (e as de provas encerradas, que não recebem envio novo) só mudam quando
alguém refaz o agrupamento. Rodar uma vez depois de atualizar. Só mostra números.

Uso:
    cd backend
    venv/bin/python scripts/reagrupar.py
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.cluster import cluster_question  # noqa: E402
from app.models.database import SessionLocal  # noqa: E402
from app.models.orm import Question  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        ids = [q.id for q in db.query(Question.id).all()]
        agrupadas = sum(1 for qid in ids if cluster_question(qid, db) is not None)
        print(f"{agrupadas} de {len(ids)} questões com grupos (as outras têm menos de 3 alunos).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
