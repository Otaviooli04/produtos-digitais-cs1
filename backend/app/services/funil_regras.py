"""Regras do funil da turma, sobre registros simples e sem banco.

A leitura fica em `funil_service`. Aqui só entra o que já foi lido, por isso
cada conta se testa com listas montadas à mão."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

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

VERMELHO = "vermelho"
AMARELO = "amarelo"
LIMITE_VERMELHO = timedelta(days=14)
LIMITE_AMARELO = timedelta(days=7)
ERROS_SEGUIDOS = 5

MOTIVO_SEM_ENVIO_LONGO = "Mais de 14 dias sem envio"
MOTIVO_PAROU_DEPOIS_DE_ERRAR = "Parou depois de errar"
MOTIVO_SEM_ENVIO = "7 a 14 dias sem envio"
MOTIVO_ERROS_SEGUIDOS = "5 erros seguidos na mesma questão"


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


def aquisicao(matriculas: list[Matricula], alunos_previstos: int | None) -> dict:
    """A primeira matrícula da turma marca a divulgação do código, e a primeira
    semana conta a partir dela."""
    primeira_semana = 0
    if matriculas:
        divulgacao = min(m.entrada for m in matriculas)
        primeira_semana = sum(1 for m in matriculas if m.entrada <= divulgacao + JANELA)
    return {
        "matriculados": len(matriculas),
        "alunos_previstos": alunos_previstos,
        "taxa_matriculados": taxa(len(matriculas), alunos_previstos),
        "primeira_semana": primeira_semana,
        "taxa_primeira_semana": taxa(primeira_semana, alunos_previstos),
        "meta": META_AQUISICAO,
    }


def alunos_ativados(matriculas: list[Matricula],
                    corrigidos: list[tuple[int, datetime]]) -> set[int]:
    """Quem corrigiu um erro entre a própria matrícula e JANELA depois dela."""
    entrada = {m.aluno: m.entrada for m in matriculas}
    return {
        aluno for aluno, momento in corrigidos
        if aluno in entrada and entrada[aluno] <= momento <= entrada[aluno] + JANELA
    }


def ativacao(matriculas: list[Matricula], tentativas: list[Tentativa],
             corrigidos: list[tuple[int, datetime]]) -> dict:
    matriculados = {m.aluno for m in matriculas}
    ativados = alunos_ativados(matriculas, corrigidos)
    return {
        "matriculados": len(matriculados),
        "com_primeiro_envio": len({t.aluno for t in tentativas} & matriculados),
        "ativados": len(ativados),
        "taxa": taxa(len(ativados), len(matriculados)),
        "meta": META_ATIVACAO,
    }


def retencao_da_semana(semana: str, matriculas: list[Matricula],
                       tentativas: list[Tentativa]) -> dict:
    """Quem enviou na semana e já tinha enviado antes dela. Por conta própria é
    o mesmo, com o envio da semana em atividade de treino ou na trilha."""
    inicio = datetime.combine(date.fromisoformat(semana), time.min)
    fim = inicio + timedelta(weeks=1)
    base = {m.aluno for m in matriculas if m.entrada < fim}
    antes = {t.aluno for t in tentativas if t.momento < inicio}
    na_semana = [t for t in tentativas if inicio <= t.momento < fim]
    voltaram = {t.aluno for t in na_semana} & antes & base
    proprios = {t.aluno for t in na_semana if t.por_conta_propria} & antes & base
    return {
        "semana": semana,
        "base": len(base),
        "voltaram": len(voltaram),
        "por_conta_propria": len(proprios),
        "taxa": taxa(len(voltaram), len(base)),
        "taxa_por_conta_propria": taxa(len(proprios), len(base)),
    }


def retencao(matriculas: list[Matricula], tentativas: list[Tentativa], agora: datetime) -> dict:
    """O cartão usa a última semana completa: a atual começa toda segunda perto
    de zero e pareceria queda."""
    semanas = [retencao_da_semana(s, matriculas, tentativas) for s in ultimas_semanas(agora)]
    return {"semanas": semanas, "ultima_completa": semanas[-2], "meta": META_RETENCAO}


def _questoes_em_aberto(serie: list[Tentativa],
                        questoes_abertas: dict[int, int | None]) -> dict[int, int]:
    """Questão aberta sem acerto em que o aluno ainda pode enviar, com quantos
    erros ele já tem nela. Quem gastou o teto não tem mais o que fazer ali."""
    por_questao: dict[int, list[Tentativa]] = defaultdict(list)
    for t in serie:
        if t.origem == LISTA:
            por_questao[t.item_id].append(t)
    em_aberto = {}
    for questao_id, teto in questoes_abertas.items():
        feitas = por_questao.get(questao_id, [])
        if any(t.resultado == ACERTO for t in feitas):
            continue
        if teto is not None and len(feitas) >= teto:
            continue
        em_aberto[questao_id] = sum(1 for t in feitas if t.resultado == ERRO)
    return em_aberto


def _cor(parado: timedelta, ultimo: Tentativa | None,
         em_aberto: dict[int, int]) -> tuple[str | None, str | None]:
    if parado > LIMITE_VERMELHO:
        return VERMELHO, MOTIVO_SEM_ENVIO_LONGO
    parou_no_erro = (
        ultimo is not None and ultimo.origem == LISTA
        and ultimo.resultado == ERRO and ultimo.item_id in em_aberto
    )
    if parado > LIMITE_AMARELO and parou_no_erro:
        return VERMELHO, MOTIVO_PAROU_DEPOIS_DE_ERRAR
    if parado >= LIMITE_AMARELO:
        return AMARELO, MOTIVO_SEM_ENVIO
    if any(erros >= ERROS_SEGUIDOS for erros in em_aberto.values()):
        return AMARELO, MOTIVO_ERROS_SEGUIDOS
    return None, None


def saude(matriculas: list[Matricula], tentativas: list[Tentativa],
          questoes_abertas: dict[int, int | None], agora: datetime) -> dict:
    """Só entra em risco quem ainda tem questão aberta para resolver (RN09). A
    trilha conta como envio, mas nunca vira motivo: o professor não vê a trilha."""
    por_aluno: dict[int, list[Tentativa]] = defaultdict(list)
    for t in _em_ordem(tentativas):
        por_aluno[t.aluno].append(t)

    listas: dict[str, list[dict]] = {VERMELHO: [], AMARELO: []}
    for m in matriculas:
        serie = por_aluno.get(m.aluno, [])
        em_aberto = _questoes_em_aberto(serie, questoes_abertas)
        if not em_aberto:
            continue
        ultimo = serie[-1] if serie else None
        # A trilha não tem turma, então o último envio pode ser de antes da
        # matrícula. Nesse caso o relógio começa na entrada.
        parado = agora - (max(ultimo.momento, m.entrada) if ultimo else m.entrada)
        cor, motivo = _cor(parado, ultimo, em_aberto)
        if cor is None:
            continue
        listas[cor].append({
            "student_id": m.aluno,
            "nome": m.nome,
            "motivo": motivo,
            "dias_sem_envio": parado.days,
            "ultimo_envio": ultimo.momento.isoformat() if ultimo else None,
        })
    for alunos in listas.values():
        alunos.sort(key=lambda a: (-a["dias_sem_envio"], a["nome"]))
    return {
        "vermelho": listas[VERMELHO],
        "amarelo": listas[AMARELO],
        "taxa_vermelho": taxa(len(listas[VERMELHO]), len(matriculas)),
        "meta": META_VERMELHO,
    }


def montar_funil(matriculas: list[Matricula], tentativas: list[Tentativa],
                 questoes_abertas: dict[int, int | None], alunos_previstos: int | None,
                 agora: datetime) -> dict:
    corrigidos = erros_corrigidos(tentativas)
    return {
        "north_star": north_star(corrigidos, agora),
        "aquisicao": aquisicao(matriculas, alunos_previstos),
        "ativacao": ativacao(matriculas, tentativas, corrigidos),
        "retencao": retencao(matriculas, tentativas, agora),
        "saude": saude(matriculas, tentativas, questoes_abertas, agora),
        "protecao": protecao(tentativas),
    }
