"""Início do aluno: o que chegou para ele, onde ele parou e o que vence logo.

Monta o painel e não grava nada. As novidades vêm do `novidades_service`, e o
resto sai do histórico unificado (`ler_historico`), o mesmo do progresso e da
trilha, para os três concordarem sobre o que está resolvido. A regra mora em
funções puras sobre registros simples, testadas sem banco."""
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.services.funil_regras import ANTECEDENCIA_DA_PROVA
from app.services.historico_do_aluno import ACERTO, FALHA, LISTA, Envio

# Quanto antes de fechar uma atividade aberta aparece em "Prazos próximos".
JANELA_DO_PRAZO = timedelta(days=7)

EM_ANDAMENTO = "em_andamento"
PROXIMA = "proxima"


@dataclass(frozen=True)
class ItemDisponivel:
    """Questão ou exercício que ainda aceita envio, com o que o cartão mostra."""
    origem: str
    item_id: int
    titulo: str
    turma_nome: str = ""
    exam_id: int | None = None
    question_number: str | None = None
    exercicio_id: int | None = None


@dataclass(frozen=True)
class AtividadeDoPainel:
    """Atividade publicada de uma turma do aluno, com a situação no instante do
    painel e se ainda há questão sem acerto e com tentativa sobrando."""
    exam_id: int
    titulo: str
    turma_nome: str
    modo: str
    situacao: str
    abre_em: datetime | None
    fecha_em: datetime | None
    criada_em: datetime | None
    com_o_que_fazer: bool


def escolher_continuar(envios: list[Envio], disponiveis: dict[tuple[str, int], ItemDisponivel],
                       proxima: dict | None) -> dict | None:
    """O item mais recente em que o aluno enviou algo, ainda sem acerto e que
    ainda aceita envio. Sem nenhum, a próxima atividade, que pode ser vazia."""
    resolvidos = {(e.origem, e.item_id) for e in envios if e.resultado == ACERTO}
    for envio in reversed(envios):
        chave = (envio.origem, envio.item_id)
        if chave in resolvidos or chave not in disponiveis:
            continue
        do_item = [e for e in envios if (e.origem, e.item_id) == chave]
        item = disponiveis[chave]
        return {
            "origem": item.origem,
            "situacao": EM_ANDAMENTO,
            "titulo": item.titulo,
            "turma_nome": item.turma_nome,
            "tentativas": len(do_item),
            "ultimo_erro": "" if do_item[-1].resultado == FALHA else do_item[-1].categoria,
            "exam_id": item.exam_id,
            "question_number": item.question_number,
            "exercicio_id": item.exercicio_id,
        }
    return proxima


def proxima_atividade(atividades: list[AtividadeDoPainel]) -> dict | None:
    """Entre as abertas com o que fazer, a que fecha primeiro. As sem data de
    fechamento vêm depois, da criada mais recentemente para a mais antiga."""
    abertas = [a for a in atividades if a.situacao == "aberta" and a.com_o_que_fazer]
    com_prazo = sorted((a for a in abertas if a.fecha_em), key=lambda a: a.fecha_em)
    sem_prazo = sorted((a for a in abertas if not a.fecha_em),
                       key=lambda a: a.criada_em or datetime.min, reverse=True)
    fila = com_prazo + sem_prazo
    if not fila:
        return None
    atividade = fila[0]
    return {
        "origem": LISTA,
        "situacao": PROXIMA,
        "titulo": atividade.titulo,
        "turma_nome": atividade.turma_nome,
        "tentativas": 0,
        "ultimo_erro": "",
        "exam_id": atividade.exam_id,
        "question_number": None,
        "exercicio_id": None,
    }


def prazos_proximos(atividades: list[AtividadeDoPainel], agora: datetime) -> list[dict]:
    """O que fecha nos próximos 7 dias e o que abre nos próximos 3, a mesma
    janela da prova chegando no funil. Só atividade com o que fazer, e cada uma
    uma vez só."""
    prazos = []
    for a in atividades:
        if not a.com_o_que_fazer:
            continue
        if a.situacao == "aberta" and a.fecha_em and agora < a.fecha_em <= agora + JANELA_DO_PRAZO:
            prazos.append((a.fecha_em, "fecha", a))
        elif a.situacao == "agendada" and a.abre_em and a.abre_em <= agora + ANTECEDENCIA_DA_PROVA:
            prazos.append((a.abre_em, "abre", a))
    prazos.sort(key=lambda p: (p[0], p[2].exam_id))
    return [
        {"exam_id": a.exam_id, "titulo": a.titulo, "turma_nome": a.turma_nome,
         "modo": a.modo, "tipo": tipo, "quando": quando.isoformat()}
        for quando, tipo, a in prazos
    ]
