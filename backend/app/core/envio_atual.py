"""O estado atual de um aluno numa questão é o último envio dele.

Com várias tentativas, contar todos os envios mostraria como erro quem já
corrigiu. As telas que dizem onde a turma está agora (grupos, resultados,
desempenho) olham só o envio atual de cada aluno. O histórico continua na aba
Respostas, no detalhe do aluno e no funil, que conta erros corrigidos.
"""

CORRETO = "Correto"


def chave_do_aluno(envio) -> tuple:
    """Quem enviou: a conta do aluno, ou o rótulo no envio em lote, que não tem
    conta. Sem nenhum dos dois, o envio vale por si."""
    if envio.student_id:
        return ("conta", envio.student_id)
    if envio.matricula:
        return ("rotulo", envio.matricula)
    return ("envio", envio.id)


def atuais_por_aluno(envios) -> list:
    """O envio atual de cada aluno, na ordem em que chegaram.

    É o último, com uma exceção: quem já acertou continua no último acerto,
    mesmo que tenha enviado algo pior depois. É o que o aluno vê (a questão
    fica resolvida) e o que o aproveitamento conta."""
    atual = {}
    for envio in sorted(envios, key=lambda e: e.id):
        chave = chave_do_aluno(envio)
        anterior = atual.get(chave)
        if (anterior is not None and anterior.error_category == CORRETO
                and envio.error_category != CORRETO):
            continue
        atual[chave] = envio
    return sorted(atual.values(), key=lambda e: e.id)
