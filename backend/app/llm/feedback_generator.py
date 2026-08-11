import json
import re

from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY


def generate_cluster_insights(question_statement: str, clusters: list[dict]) -> list[dict]:
    """Gera um insight pedagógico por grupo em uma única chamada ao Gemini (uma
    requisição por questão). Cada item precisa de cluster_id, size, dominant_error e representative_code."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")
    if not clusters:
        return []

    client = genai.Client(api_key=GEMINI_API_KEY)

    blocos = "\n\n".join(
        f"""[Cluster {c["cluster_id"]}] — erro predominante: {c["dominant_error"]}; {c["size"]} aluno(s)
Código representativo (com nº de linha):
```c
{_numbered(c["representative_code"])}
```"""
        for c in clusters
    )

    prompt = f"""
Você é um assistente pedagógico especializado em ensino de programação introdutória em C.

Enunciado da questão:
{question_statement}

Abaixo estão grupos de alunos com padrões de erro similares. Para CADA grupo, gere:
- "insight": insight pedagógico conciso para o professor, contendo o que esse grupo
  errou ou não compreendeu e uma sugestão de intervenção didática (máx. 4 frases);
- "highlight_lines": a lista dos NÚMEROS DE LINHA (conforme prefixados no código
  representativo) onde está o problema que define o grupo. Aponte apenas as linhas
  diretamente responsáveis pelo erro (não o trecho inteiro). Use [] se o código
  estiver correto ou se não houver uma linha específica a culpar.

Seja direto e objetivo.

{blocos}

Retorne APENAS um JSON: uma lista de objetos, um por grupo, no formato
{{"cluster_id": <int>, "insight": "<texto>", "highlight_lines": [<int>, ...]}}.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    parsed = _parse_insights(response.text)
    by_id = {item.get("cluster_id"): item for item in parsed}

    return [
        {
            "cluster_id": c["cluster_id"],
            "size": c["size"],
            "dominant_error": c["dominant_error"],
            "insight": (by_id.get(c["cluster_id"], {}).get("insight") or "").strip(),
            "highlight_lines": _clean_lines(
                by_id.get(c["cluster_id"], {}).get("highlight_lines"),
                c["representative_code"],
            ),
        }
        for c in clusters
    ]


def _numbered(code: str) -> str:
    """Prefixa cada linha com seu número (1-based) p/ o modelo referenciar com precisão."""
    return "\n".join(f"{i}: {ln}" for i, ln in enumerate((code or "").split("\n"), 1))


def _clean_lines(raw, code: str) -> list[int]:
    """Sanitiza as linhas devolvidas pelo modelo: inteiros únicos, ordenados e dentro
    do intervalo do código (descarta alucinação de linha inexistente)."""
    if not isinstance(raw, list):
        return []
    max_line = len((code or "").split("\n"))
    out: set[int] = set()
    for v in raw:
        try:
            n = int(v)
        except (TypeError, ValueError):
            continue
        if 1 <= n <= max_line:
            out.add(n)
    return sorted(out)


def _parse_insights(text: str) -> list[dict]:
    """Parsing defensivo: o modelo às vezes embrulha em ```json``` ou devolve
    {"insights": [...]} em vez da lista crua."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return []
    if isinstance(data, dict):
        for key in ("insights", "clusters", "data"):
            if isinstance(data.get(key), list):
                return data[key]
        return []
    if isinstance(data, list):
        return data
    return []
