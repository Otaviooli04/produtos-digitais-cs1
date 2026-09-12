"""Exercício de treino gerado sob medida para o erro que o aluno repete.

Diferente de `student_explainer`, que explica o que já aconteceu, aqui o modelo
produz o que vem depois: um exercício novo, no nível da disciplina, que obriga o
aluno a enfrentar de novo a dificuldade que ele acumula.

Três restrições vêm direto dos riscos do produto:
- **nunca vale nota.** O gerado é treino, e por isso não passa por revisão do
  professor. O preço dessa escolha é que o aluno pode reportar um exercício ruim;
- **não entregar a solução.** O enunciado descreve o problema e os casos de
  teste, nunca o código;
- **custo por aluno.** Geração é chamada de LLM por aluno, então existe teto
  diário e reaproveitamento do que já foi gerado e não foi resolvido.
"""
import json
import re

from google import genai
from google.genai import types

from app.core.config import GEMINI_API_KEY

MODELO = "gemini-2.5-flash"

# Teto de custo. Acima disso o aluno continua treinando no que já foi gerado,
# que é ilimitado, mas não gera exercício novo hoje.
GERACOES_POR_DIA = 8


class ExercicioInvalido(RuntimeError):
    """O modelo devolveu algo que não dá para usar como exercício."""


def gerar_exercicio(error_category: str, diagnostico: str, exemplos: list[str]) -> dict:
    """Devolve `{titulo, enunciado, casos_teste, required_structures}`.

    `exemplos` são enunciados que o aluno já viu, só para o modelo não repetir o
    mesmo problema com outras palavras."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=MODELO,
        contents=_montar_prompt(error_category, diagnostico, exemplos),
        config=types.GenerateContentConfig(temperature=0.7, response_mime_type="application/json"),
    )
    return _validar(response.text or "")


def _montar_prompt(error_category: str, diagnostico: str, exemplos: list[str]) -> str:
    ja_vistos = ""
    if exemplos:
        lista = "\n".join(f"- {e[:200]}" for e in exemplos[:5])
        ja_vistos = f"\nO aluno já treinou com estes enunciados, então proponha outro problema:\n{lista}\n"

    return f"""
Você monta exercícios para uma disciplina introdutória de programação em C, a
primeira da graduação. Um aluno repete o seguinte erro:

Categoria: {error_category}
O que o sistema diagnostica: {diagnostico}
{ja_vistos}
Crie UM exercício curto que force o aluno a enfrentar exatamente essa
dificuldade, no nível de quem está aprendendo C agora.

Responda apenas com JSON neste formato:
{{
  "titulo": "quatro a seis palavras",
  "enunciado": "o problema, incluindo o formato exato da entrada e da saída",
  "casos_teste": [
    {{"input": "entrada exata, com quebras de linha se houver", "expected_output": "saída exata"}}
  ],
  "required_structures": ["For"]
}}

Regras obrigatórias:
- Entre 3 e 5 casos de teste, e pelo menos um no limite do problema, que é onde
  o erro desta categoria costuma aparecer.
- A entrada e a saída precisam ser exatas: o corretor compara texto, caractere
  por caractere. Não escreva mensagens como "Digite um número".
- A saída esperada termina em quebra de linha implícita, não escreva "\\n".
- `required_structures` só com os valores: For, While, DoWhile, If, Switch,
  Function, Recursion, Array, Pointer. Use lista vazia se nada for obrigatório.
- Não escreva a solução, nem trechos de código em C, em lugar nenhum.
- Português do Brasil.
"""


ESTRUTURAS_VALIDAS = {
    "For", "While", "DoWhile", "If", "Switch", "Function", "Recursion", "Array", "Pointer",
}


def _validar(texto: str) -> dict:
    """O modelo às vezes embrulha o JSON em cerca de markdown, e às vezes inventa
    campo. O que não passa daqui não vira exercício."""
    bruto = texto.strip()
    bruto = re.sub(r"^```(?:json)?\s*|\s*```$", "", bruto).strip()
    try:
        dados = json.loads(bruto)
    except json.JSONDecodeError as e:
        raise ExercicioInvalido(f"resposta não é JSON: {e}") from e

    enunciado = (dados.get("enunciado") or "").strip()
    titulo = (dados.get("titulo") or "").strip() or "Exercício de treino"
    casos = dados.get("casos_teste") or []

    if len(enunciado) < 20:
        raise ExercicioInvalido("enunciado vazio ou curto demais")
    if not isinstance(casos, list) or not casos:
        raise ExercicioInvalido("exercício sem caso de teste")

    limpos = []
    for caso in casos:
        if not isinstance(caso, dict):
            continue
        esperado = str(caso.get("expected_output", ""))
        if not esperado.strip():
            continue
        limpos.append({
            "input": str(caso.get("input", "")),
            "expected_output": esperado,
        })
    if not limpos:
        raise ExercicioInvalido("nenhum caso de teste utilizável")

    estruturas = [
        e for e in (dados.get("required_structures") or [])
        if isinstance(e, str) and e in ESTRUTURAS_VALIDAS
    ]
    return {
        "titulo": titulo[:120],
        "enunciado": enunciado,
        "casos_teste": limpos[:5],
        "required_structures": estruturas,
    }
