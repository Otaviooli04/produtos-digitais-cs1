"""Histórico do aluno: os envios das listas e as tentativas da trilha numa
lista só, em ordem de tempo.

O progresso, os erros recorrentes e a trilha leem daqui, então os três sempre
concordam sobre o que o aluno errou e o que ele já superou. A classificação de
cada envio também mora aqui, e o funil da turma usa a mesma."""

CATEGORIA_CORRETA = "Correto"
# O que as heurísticas devolvem quando a execução falha por fora do código do
# aluno, como o Docker fora do ar. Não é erro dele.
CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"

ACERTO = "acerto"
ERRO = "erro"
FALHA = "falha"

LISTA = "lista"
TRILHA = "trilha"


def resultado_da_lista(error_category: str | None) -> str:
    if error_category == CATEGORIA_CORRETA:
        return ACERTO
    if not error_category or error_category == CATEGORIA_FALHA_TECNICA:
        return FALHA
    return ERRO


def resultado_da_trilha(all_tests_passed: bool | None, error_category: str | None) -> str:
    if all_tests_passed:
        return ACERTO
    if not error_category or error_category == CATEGORIA_FALHA_TECNICA:
        return FALHA
    return ERRO
