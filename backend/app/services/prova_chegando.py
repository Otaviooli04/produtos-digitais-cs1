"""Prova chegando (experimento 5): o treino curto que o Início oferece nos três
dias antes de uma prova abrir. Funções puras sobre registros simples, testadas
sem banco. O cartão é calculado na hora, sem tabela própria."""
from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.models.orm import Exam
from app.services.funil_regras import ANTECEDENCIA_DA_PROVA
from app.services.historico_do_aluno import ACERTO, TRILHA, Envio, Erro

if TYPE_CHECKING:
    from app.services.inicio_service import AtividadeDoPainel

MAXIMO_DE_ERROS = 3


def prova_na_janela(atividades: list[AtividadeDoPainel], agora: datetime) -> AtividadeDoPainel | None:
    """A prova agendada que abre nos próximos 3 dias e ainda tem o que fazer. Com
    mais de uma, a que abre primeiro, e no empate a de menor id."""
    na_janela = [
        a for a in atividades
        if a.modo == Exam.MODO_PROVA and a.situacao == "agendada" and a.com_o_que_fazer
        and a.abre_em and a.abre_em - ANTECEDENCIA_DA_PROVA <= agora < a.abre_em
    ]
    return min(na_janela, key=lambda a: (a.abre_em, a.exam_id), default=None)


def erros_do_treino(erros: list[Erro], envios: list[Envio], inicio_da_janela: datetime) -> list[dict]:
    """Os feitos primeiro, em ordem do acerto, depois os ativos na ordem de
    `erros_do_aluno`, até o máximo. Um erro feito não volta atrás dentro da
    janela. O acerto com a própria categoria do alvo não conta, como em
    `erros_do_aluno`: violação de estrutura e aviso saem antes dos testes, então
    o exercício passa com o erro ainda ali."""
    conhecidos = {erro.categoria for erro in erros}
    feitos: list[str] = []
    for envio in envios:
        if (envio.origem == TRILHA and envio.resultado == ACERTO
                and envio.categoria != envio.alvo and envio.momento >= inicio_da_janela
                and envio.alvo in conhecidos and envio.alvo not in feitos):
            feitos.append(envio.alvo)
    pendentes = [erro.categoria for erro in erros if erro.ativo and erro.categoria not in feitos]
    itens = ([{"error_category": c, "feito": True} for c in feitos]
             + [{"error_category": c, "feito": False} for c in pendentes])
    return itens[:MAXIMO_DE_ERROS]


def montar_cartao(atividade: AtividadeDoPainel, erros: list[Erro], envios: list[Envio]) -> dict | None:
    """O cartão da prova, ou nada quando o aluno não tem erro para treinar."""
    itens = erros_do_treino(erros, envios, atividade.abre_em - ANTECEDENCIA_DA_PROVA)
    if not itens:
        return None
    return {
        "exam_id": atividade.exam_id,
        "titulo": atividade.titulo,
        "turma_nome": atividade.turma_nome,
        "abre_em": atividade.abre_em.isoformat(),
        "erros": itens,
    }


def primeiro_pendente(cartao: dict) -> str | None:
    """A categoria do primeiro erro da lista que ainda não está feito."""
    return next((e["error_category"] for e in cartao["erros"] if not e["feito"]), None)
