"""O estado atual de um aluno numa questão é o último envio dele.

Com várias tentativas, contar todos os envios mostraria como erro quem já
corrigiu. As telas que dizem onde a turma está agora (grupos, resultados,
desempenho) olham só o último envio de cada aluno. O histórico continua na aba
Respostas, no detalhe do aluno e no funil, que conta erros corrigidos.
"""


def chave_do_aluno(envio) -> tuple:
    """Quem enviou: a conta do aluno, ou o rótulo no envio em lote, que não tem
    conta. Sem nenhum dos dois, o envio vale por si."""
    if envio.student_id:
        return ("conta", envio.student_id)
    if envio.matricula:
        return ("rotulo", envio.matricula)
    return ("envio", envio.id)


def ultimos_por_aluno(envios) -> list:
    """O último envio de cada aluno, na ordem em que chegaram."""
    ultimos = {}
    for envio in sorted(envios, key=lambda e: e.id):
        ultimos[chave_do_aluno(envio)] = envio
    return sorted(ultimos.values(), key=lambda e: e.id)
