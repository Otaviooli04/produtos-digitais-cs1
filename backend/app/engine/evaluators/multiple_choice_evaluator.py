def evaluate_multiple_choice(answer: str, expected: str) -> dict:
    correct = answer.strip().upper() == expected.strip().upper()
    return {
        "correct": correct,
        "answer": answer,
        "expected": expected,
    }
