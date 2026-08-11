from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.orm import Exam, Question


def get_exam_or_404(exam_id: int, db: Session, professor_id: int | None = None) -> Exam:
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Prova não encontrada.")
    if professor_id is not None:
        if exam.turma_id is None or exam.turma is None or exam.turma.professor_id != professor_id:
            raise HTTPException(status_code=404, detail="Prova não encontrada.")
    return exam


def get_question_or_404(exam_id: int, question_number: str, db: Session, professor_id: int | None = None) -> Question:
    exam = get_exam_or_404(exam_id, db, professor_id)
    question = db.query(Question).filter(
        Question.exam_id == exam.id,
        Question.number == question_number,
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Questão não encontrada.")
    return question
