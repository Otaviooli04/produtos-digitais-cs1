from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY


def extract_exam_structure(raw_text: str, *, file_bytes: bytes = None,
                           mime_type: str = None) -> dict:
    """Extrai a estrutura da prova via Gemini. Para PDF, envia o arquivo nativo ao
    modelo multimodal (preserva o layout das tabelas); para DOCX/fallback, usa o texto."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY não configurada.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
Você é um analisador de provas de programação introdutória em C.
Leia o texto da prova abaixo e extraia apenas as questões de programação (que pedem ao aluno para escrever código C).
Ignore questões dissertativas, de múltipla escolha ou teóricas.

Para cada questão de código, extraia:
- "number": número ou identificador da questão (string)
- "type": sempre "code"
- "statement": enunciado completo da questão
- "required_structures": estruturas de controle EXPLICITAMENTE exigidas pelo enunciado — valores possíveis: "If","For","While","DoWhile","Switch" (lista vazia se não especificado; veja as regras abaixo)
- "forbidden_structures": estruturas explicitamente proibidas (lista vazia se não houver)
- "requires_loop": true se o enunciado exige laço de repetição, false caso contrário
- "required_functions": funções que o enunciado EXIGE que o aluno implemente (lista vazia se a questão não pede funções específicas)
- "test_cases": casos de teste de exemplo presentes no enunciado (lista vazia se não houver)

Cada item de "required_functions" é um objeto com:
- "name": nome exato da função exigida (string)
- "param_count": número de parâmetros exigidos (inteiro), ou null se o enunciado não especificar
- "return_type": tipo de retorno em C exigido, ex: "int", "float", "void", "char" (string), ou null se não especificado
- "requires_recursion": true SOMENTE se o enunciado exigir explicitamente que a função seja recursiva, false caso contrário
- "requires_pointer_param": true SOMENTE se o enunciado exigir passagem por referência / ponteiro (ex: "altere o valor", "por referência", "usando ponteiros"), false caso contrário

Regras para "required_functions":
- Extraia apenas funções que o enunciado obriga o aluno a CRIAR (ex: "implemente uma função fatorial", "crie a função int soma(int a, int b)").
- NÃO inclua funções de biblioteca (printf, scanf, malloc, etc.) nem a função main.
- Se a assinatura aparecer no enunciado (ex: "int soma(int a, int b)"), preencha name, param_count e return_type a partir dela.
- Na dúvida sobre param_count ou return_type, use null em vez de adivinhar.
- requires_recursion e requires_pointer_param só são true quando o enunciado pede isso de forma explícita.

Regras para "required_structures" e "forbidden_structures":
- Inclua uma estrutura SOMENTE quando o enunciado a menciona de forma EXPLÍCITA (ex.: "utilize um laço", "resolva com estrutura de repetição", "use um comando condicional", "sem usar while").
- NÃO infira a estrutura a partir da lógica do problema. Se o problema "naturalmente" precisaria de um if/for mas o enunciado não exige isso em palavras, deixe a lista VAZIA. Existem múltiplas soluções corretas; exigir uma estrutura não pedida reprova código certo.
- "requires_loop" segue a mesma régua: true apenas quando o enunciado pede repetição (incluindo ler/processar N valores), false caso contrário.

Cada item de "test_cases" é um objeto com:
- "input": a entrada exata que o programa recebe via stdin (string). Se houver vários valores, separe-os exatamente como o programa os lê (em geral por espaço ou quebra de linha). Use string vazia se a questão não exige entrada.
- "expected_output": a saída exata que o PROGRAMA imprime (string). Use "\\n" SOMENTE quando o programa realmente imprime em múltiplas linhas (ex.: uma matriz linha a linha, ou printf com "\\n").

Regras para "test_cases":
- Extraia os exemplos das tabelas/listas "Por exemplo", "Input/Resultado", "Entrada/Saída" ou "Input/Esperado" presentes no enunciado.
- Reproduza os valores EXATAMENTE como aparecem; NÃO invente casos nem normalize espaçamento de matrizes/colunas.
- ATENÇÃO às quebras de linha falsas do layout: se uma saída longa (ex.: uma lista de números numa única linha) aparece quebrada em duas linhas apenas porque o texto não coube na largura da página/coluna da tabela, isso NÃO é uma quebra real — junte tudo numa só linha. Se o enunciado diz "imprima em uma única linha", "em uma linha" ou "separados por um único caractere", a expected_output deve ter UMA linha só.
- Inclua a quebra real apenas quando a estrutura de linhas faz parte da saída do programa (matrizes, um valor por linha, etc.).
- Ignore colunas de status ("Got", "Resultado obtido", ✓/✗) — interessa apenas a entrada e a saída esperada.
- Lista vazia se o enunciado não traz exemplos de entrada/saída.

Retorne apenas o JSON com a chave "questions" contendo a lista de questões de código.
"""

    if file_bytes and mime_type == "application/pdf":
        contents = [
            types.Part.from_bytes(data=file_bytes, mime_type="application/pdf"),
            prompt + "\n\nLeia DIRETAMENTE o PDF anexado e preserve o layout exato "
                     "das tabelas de exemplo (matrizes, colunas alinhadas, casas decimais).",
        ]
    else:
        contents = prompt + f"\n\nTexto da prova:\n{raw_text}"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    import json
    import re
    text = response.text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    data = json.loads(text)

    # O modelo às vezes ignora o invólucro e devolve a lista de questões direto;
    # normaliza para sempre retornar {"questions": [...]}.
    if isinstance(data, list):
        return {"questions": data}
    if isinstance(data, dict) and "questions" not in data:
        return {"questions": []}
    return data
