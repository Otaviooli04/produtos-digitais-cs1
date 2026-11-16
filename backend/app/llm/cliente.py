"""Cliente do Gemini com tempo limite.

Sem ele, uma chamada travada segura a requisição do aluno ou do professor sem
prazo, e a tela fica carregando para sempre. Estourado o tempo, a chamada
levanta erro e cada ponto de uso já trata a falha como hoje."""
from google import genai
from google.genai import types

TEMPO_PADRAO_S = 30
# A extração recebe o PDF inteiro da prova e roda em segundo plano.
TEMPO_DA_EXTRACAO_S = 120


def cliente_gemini(api_key: str, segundos: int = TEMPO_PADRAO_S) -> genai.Client:
    return genai.Client(api_key=api_key,
                        http_options=types.HttpOptions(timeout=segundos * 1000))
