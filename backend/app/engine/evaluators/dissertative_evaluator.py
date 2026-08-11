from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY


def evaluate_dissertative(answer: str, rubric: str) -> dict:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Você é um corretor pedagógico de provas de programação introdutória.
Avalie a resposta do aluno com base na rubrica fornecida pelo professor.

Rubrica: {rubric}

Resposta do aluno: {answer}

Retorne um JSON com:
- "score": nota de 0.0 a 1.0 (proporção de acerto)
- "feedback": comentário formativo explicando o que está correto e o que falta
- "missing_points": lista de pontos da rubrica não atendidos
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    import json
    return json.loads(response.text)
