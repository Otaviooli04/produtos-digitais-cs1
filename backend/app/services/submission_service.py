from sqlalchemy.orm import Session
from app.engine.evaluators.code_evaluator import evaluate_code
from app.models.orm import Question, Submission, SubmissionTestResult


def evaluate_submission(exam_id: int, question_number: str, code: str, db: Session, matricula=None, dry_run=False) -> dict:
    question = db.query(Question).filter(
        Question.exam_id == exam_id,
        Question.number == question_number,
    ).first()

    if not question:
        raise ValueError(f"Questão {question_number} não encontrada na prova {exam_id}.")

    test_cases = [
        {"input": tc.input, "expected_output": tc.expected_output}
        for tc in question.test_cases
    ]

    result = evaluate_code(
        code,
        test_cases,
        question.required_structures or [],
        question.forbidden_structures or [],
        question.required_functions or [],
    )

    if dry_run:
        return {"question_number": question_number, **result}

    persist_submission(question, code, result, db, matricula=matricula)
    return {"question_number": question_number, **result}


def persist_submission(question: Question, code: str, result: dict, db: Session,
                       matricula=None, student_id=None, attempt_number: int = 1) -> Submission:
    """Grava a tentativa e seus resultados de teste. Toda submissão é persistida,
    inclusive as intermediárias — é esse histórico que sustenta o acompanhamento
    do aluno."""
    submission = Submission(
        question_id=question.id,
        code=code,
        compile_error=result["compile_error"],
        warnings=result["warnings"],
        all_tests_passed=result["all_tests_passed"],
        error_category=result["diagnosis"]["error_category"],
        pedagogical_diagnosis=result["diagnosis"]["pedagogical_diagnosis"],
        actionable_feedback=result["diagnosis"]["actionable_feedback"],
        ast_structures=result.get("ast_structures", []),
        ast_functions=result.get("ast_functions", []),
        matricula=matricula,
        student_id=student_id,
        attempt_number=attempt_number,
    )
    db.add(submission)
    db.flush()

    for tr in result["test_results"]:
        db.add(SubmissionTestResult(
            submission_id=submission.id,
            input=tr["input"],
            expected_output=tr["expected_output"],
            actual_output=tr["actual_output"],
            passed=tr["passed"],
        ))

    db.commit()
    db.refresh(submission)
    return submission


def delete_submission(submission: Submission, db: Session) -> None:
    db.delete(submission)  # test_results saem por cascade (all, delete-orphan)
    db.commit()


def reevaluate_submission(submission: Submission, db: Session) -> dict:
    """Reavalia o código já submetido contra os test cases/requisitos ATUAIS da
    questão (útil após editar casos ou requisitos). Atualiza a submissão no lugar."""
    question = submission.question
    test_cases = [
        {"input": tc.input, "expected_output": tc.expected_output}
        for tc in question.test_cases
    ]
    result = evaluate_code(
        submission.code,
        test_cases,
        question.required_structures or [],
        question.forbidden_structures or [],
        question.required_functions or [],
    )

    submission.compile_error = result["compile_error"]
    submission.warnings = result["warnings"]
    submission.all_tests_passed = result["all_tests_passed"]
    submission.error_category = result["diagnosis"]["error_category"]
    submission.pedagogical_diagnosis = result["diagnosis"]["pedagogical_diagnosis"]
    submission.actionable_feedback = result["diagnosis"]["actionable_feedback"]
    submission.ast_structures = result.get("ast_structures", [])
    submission.ast_functions = result.get("ast_functions", [])

    submission.test_results = []  # delete-orphan remove os antigos
    db.flush()
    for tr in result["test_results"]:
        db.add(SubmissionTestResult(
            submission_id=submission.id,
            input=tr["input"],
            expected_output=tr["expected_output"],
            actual_output=tr["actual_output"],
            passed=tr["passed"],
        ))
    db.commit()
    return {"question_number": question.number, **result}
