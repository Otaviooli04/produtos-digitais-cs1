"""Regras do funil da turma, sobre registros simples e sem banco.

A leitura fica em `funil_service`. Aqui só entra o que já foi lido, por isso
cada conta se testa com listas montadas à mão."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.services.calendario import semana_iso
from app.services.student_activity_service import CATEGORIA_CORRETA

# O que as heurísticas devolvem quando a execução falha por fora do código do
# aluno, como o Docker fora do ar. Não é erro dele.
CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"

ACERTO = "acerto"
ERRO = "erro"
FALHA = "falha"

LISTA = "lista"
TRILHA = "trilha"

SEMANAS = 8
JANELA = timedelta(days=7)

META_AQUISICAO = 80.0
META_ATIVACAO = 60.0
META_RETENCAO = 50.0
META_VERMELHO = 15.0


@dataclass(frozen=True)
class Tentativa:
    """Um envio do aluno, de lista ou de trilha, já classificado."""
    aluno: int
    origem: str
    item_id: int
    momento: datetime
    ordem: int
    resultado: str
    por_conta_propria: bool = False

    @property
    def item(self) -> tuple[int, str, int]:
        return (self.aluno, self.origem, self.item_id)


@dataclass(frozen=True)
class Matricula:
    aluno: int
    nome: str
    entrada: datetime


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


def taxa(parte: int, todo: int | None) -> float | None:
    return round(parte / todo * 100, 1) if todo else None


def ultimas_semanas(agora: datetime) -> list[str]:
    """As SEMANAS semanas que terminam na atual, da mais antiga para a atual."""
    atual = date.fromisoformat(semana_iso(agora))
    return [(atual - timedelta(weeks=i)).isoformat() for i in range(SEMANAS - 1, -1, -1)]


def _em_ordem(tentativas: list[Tentativa]) -> list[Tentativa]:
    return sorted(tentativas, key=lambda t: (t.momento, t.ordem))


def _por_item(tentativas: list[Tentativa]) -> dict[tuple[int, str, int], list[Tentativa]]:
    series: dict[tuple[int, str, int], list[Tentativa]] = defaultdict(list)
    for t in _em_ordem(tentativas):
        series[t.item].append(t)
    return series


def erros_corrigidos(tentativas: list[Tentativa]) -> list[tuple[int, datetime]]:
    """Aluno e momento do primeiro acerto de cada item que teve erro antes dele.
    Um por item: errar de novo depois de acertar não abre outra correção."""
    corrigidos = []
    for serie in _por_item(tentativas).values():
        errou = False
        for t in serie:
            if t.resultado == ERRO:
                errou = True
            elif t.resultado == ACERTO:
                if errou:
                    corrigidos.append((t.aluno, t.momento))
                break
    return corrigidos


def north_star(corrigidos: list[tuple[int, datetime]], agora: datetime) -> dict:
    semanas = ultimas_semanas(agora)
    por_semana = Counter(semana_iso(momento) for _, momento in corrigidos)
    return {
        "semana_atual": por_semana[semanas[-1]],
        "total": len(corrigidos),
        "semanas": [{"semana": s, "erros_corrigidos": por_semana[s]} for s in semanas],
    }


def protecao(tentativas: list[Tentativa]) -> dict:
    """Acompanha a North Star para ela não crescer pelo motivo errado, como o
    aluno tentando às cegas até passar."""
    ate_acertar = []
    de_primeira = []
    for serie in _por_item(tentativas).values():
        validas = [t for t in serie if t.resultado != FALHA]
        if not validas:
            continue
        de_primeira.append(validas[0].resultado == ACERTO)
        posicao = next((i for i, t in enumerate(validas) if t.resultado == ACERTO), None)
        if posicao is not None:
            ate_acertar.append(posicao + 1)
    media = round(sum(ate_acertar) / len(ate_acertar), 1) if ate_acertar else None
    return {
        "media_tentativas_ate_acertar": media,
        "acerto_de_primeira": taxa(sum(de_primeira), len(de_primeira)),
        "itens_com_acerto": len(ate_acertar),
    }
