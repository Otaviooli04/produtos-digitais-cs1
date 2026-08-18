"""Explicação individual da tentativa, escrita para o ALUNO.

Diferente de `feedback_generator`, que resume um grupo para o professor. Aqui o
destinatário é quem errou, então o texto fala com ele e sobre o código dele.

Duas restrições vêm direto dos riscos do produto:
- **não entregar a solução.** Se o modelo devolver o código corrigido, o aluno
  resolve a lista sem aprender e o produto vira o que ele já tem de graça;
- **custo por aluno.** A explicação é gerada sob demanda e uma única vez por
  tentativa (cacheada em `Submission.llm_explanation`).
"""
from google import genai
from google.genai import types

from app.core.config import GEMINI_API_KEY

MODELO = "gemini-2.5-flash"
LIMITE_CODIGO = 6000  # corta código absurdamente longo antes de gastar tokens


def generate_student_explanation(
    statement: str,
    code: str,
    error_category: str,
    pedagogical_diagnosis: str,
    test_results: list[dict] | None = None,
) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = _montar_prompt(statement, code, error_category, pedagogical_diagnosis, test_results)
    response = client.models.generate_content(
        model=MODELO,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.2),
    )
    return (response.text or "").strip()


def _montar_prompt(statement, code, error_category, pedagogical_diagnosis, test_results) -> str:
    falhas = _falhas_resumidas(test_results or [])
    return f"""
Você é um monitor de uma disciplina introdutória de programação em C. Um aluno
enviou a solução abaixo e ela não está correta. Explique a ELE, em português do
Brasil, por que o código dele falha.

Enunciado da questão:
{statement}

Diagnóstico automático do sistema: {error_category} — {pedagogical_diagnosis}
{falhas}

Código do aluno (com números de linha):
```c
{_numerado(code)}
```

Regras obrigatórias:
- Fale com o aluno na segunda pessoa, em no máximo 5 frases curtas.
- Aponte a linha ou o trecho responsável pelo erro e explique o RACIOCÍNIO errado
  por trás dele, não apenas o sintoma.
- NUNCA escreva a solução, nem o código corrigido, nem o trecho pronto para colar.
  Você pode citar no máximo o nome de uma função ou de um operador.
- Termine com uma pergunta ou um passo concreto que leve o aluno a achar o erro
  sozinho.
- Não use markdown, títulos nem listas. Apenas o texto corrido.
"""


def _falhas_resumidas(test_results: list[dict]) -> str:
    falhas = [t for t in test_results if not t.get("passed")][:3]
    if not falhas:
        return ""
    linhas = "\n".join(
        f'- entrada "{t.get("input", "")}": esperado "{t.get("expected_output", "")}", '
        f'obtido "{t.get("actual_output", "")}"'
        for t in falhas
    )
    return f"Casos de teste que falharam:\n{linhas}"


def _numerado(code: str) -> str:
    texto = (code or "")[:LIMITE_CODIGO]
    return "\n".join(f"{i}: {ln}" for i, ln in enumerate(texto.split("\n"), 1))
