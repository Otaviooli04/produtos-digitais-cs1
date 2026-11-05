"""Regras do funil da turma, sobre registros simples e sem banco.

A leitura fica em `funil_service`. Aqui só entra o que já foi lido, por isso
cada conta se testa com listas montadas à mão."""
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from statistics import median

from app.models.orm import Enrollment
from app.services.calendario import semana_iso
from app.services.historico_do_aluno import ACERTO, ERRO, FALHA, LISTA

SEMANAS = 8
JANELA = timedelta(days=7)
# A prova puxa o aluno desde 3 dias antes de abrir, a janela do aviso "Prova chegando".
ANTECEDENCIA_DA_PROVA = timedelta(days=3)
# A mesma janela do registro de acesso: 30 minutos sem evento encerram a sessão.
JANELA_DA_SESSAO = timedelta(minutes=30)

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
    origem: str | None = None


@dataclass(frozen=True)
class Acesso:
    """Uma abertura do app do aluno. `via` nula é abertura por conta própria."""
    aluno: int
    momento: datetime
    via: str | None = None


@dataclass(frozen=True)
class JanelaDeProva:
    """Intervalo fechado em que uma prova puxa o aluno. Lado nulo é sem limite."""
    inicio: datetime | None
    fim: datetime | None


@dataclass
class DadosDaTurma:
    """O que o serviço leu de uma turma, com a trilha e os acessos já filtrados
    pela matrícula."""
    matriculas: list[Matricula]
    tentativas: list[Tentativa]
    questoes_abertas: dict[int, int | None]
    acessos: list[Acesso] = field(default_factory=list)
    janelas: list[JanelaDeProva] = field(default_factory=list)


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


def por_origem(matriculas: list[Matricula]) -> dict:
    contagem = Counter(m.origem for m in matriculas)
    convite = contagem[Enrollment.ORIGEM_CONVITE]
    codigo = contagem[Enrollment.ORIGEM_CODIGO]
    return {"convite": convite, "codigo": codigo, "sem_origem": len(matriculas) - convite - codigo}


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
        "por_origem": por_origem(matriculas),
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


def janela_da_prova(abre_em: datetime | None, fecha_em: datetime | None) -> JanelaDeProva | None:
    """Prova sem data não puxa ninguém."""
    if abre_em is None and fecha_em is None:
        return None
    inicio = abre_em - ANTECEDENCIA_DA_PROVA if abre_em is not None else None
    return JanelaDeProva(inicio=inicio, fim=fecha_em)


def com_prova_marcada(momento: datetime, janelas: list[JanelaDeProva]) -> bool:
    return any(
        (j.inicio is None or j.inicio <= momento) and (j.fim is None or momento <= j.fim)
        for j in janelas
    )


def retencao_da_semana(semana: str, matriculas: list[Matricula], tentativas: list[Tentativa],
                       acessos: list[Acesso], janelas: list[JanelaDeProva]) -> dict:
    """Voltou quem abriu o app na semana e já tinha feito algo antes dela, acesso
    ou envio. O envio antes conta para as primeiras semanas com a tabela de
    acessos não aparecerem zeradas. Os sinais de hábito são recortes de quem voltou. Pelo
    envio é a conta da parte 1."""
    inicio = datetime.combine(date.fromisoformat(semana), time.min)
    fim = inicio + timedelta(weeks=1)
    base = {m.aluno for m in matriculas if m.entrada < fim}

    enviaram_antes = {t.aluno for t in tentativas if t.momento < inicio}
    envios_na_semana = [t for t in tentativas if inicio <= t.momento < fim]
    por_envio = {t.aluno for t in envios_na_semana} & enviaram_antes & base
    proprios = {t.aluno for t in envios_na_semana if t.por_conta_propria} & enviaram_antes & base

    ativos_antes = enviaram_antes | {a.aluno for a in acessos if a.momento < inicio}
    acessos_na_semana = [a for a in acessos if inicio <= a.momento < fim]
    voltaram = {a.aluno for a in acessos_na_semana} & ativos_antes & base
    sem_prova = {a.aluno for a in acessos_na_semana
                 if not com_prova_marcada(a.momento, janelas)} & voltaram
    sem_aviso = {a.aluno for a in acessos_na_semana if a.via is None} & voltaram
    return {
        "semana": semana,
        "base": len(base),
        "voltaram": len(voltaram),
        "taxa": taxa(len(voltaram), len(base)),
        "sem_prova_marcada": len(sem_prova),
        "taxa_sem_prova_marcada": taxa(len(sem_prova), len(base)),
        "sem_aviso": len(sem_aviso),
        "taxa_sem_aviso": taxa(len(sem_aviso), len(base)),
        "voltaram_por_envio": len(por_envio),
        "taxa_por_envio": taxa(len(por_envio), len(base)),
        "por_conta_propria": len(proprios),
        "taxa_por_conta_propria": taxa(len(proprios), len(base)),
    }


def retencao(matriculas: list[Matricula], tentativas: list[Tentativa], acessos: list[Acesso],
             janelas: list[JanelaDeProva], agora: datetime) -> dict:
    """O cartão usa a última semana completa: a atual começa toda segunda perto
    de zero e pareceria queda."""
    semanas = [retencao_da_semana(s, matriculas, tentativas, acessos, janelas)
               for s in ultimas_semanas(agora)]
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
        # Um envio de lista religado pela matrícula institucional pode ser de
        # antes da matrícula. Nesse caso o relógio começa na entrada.
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


def fim_da_sessao(entrada: datetime, momentos: list[datetime]) -> datetime:
    """Último instante da sessão que começa na matrícula. Ela segue enquanto cada
    evento vem até JANELA_DA_SESSAO depois do anterior."""
    fim = entrada
    for momento in sorted(m for m in momentos if m >= entrada):
        if momento - fim > JANELA_DA_SESSAO:
            break
        fim = momento
    return fim


def sucesso(matriculas: list[Matricula], tentativas: list[Tentativa], acessos: list[Acesso],
            corrigidos: list[tuple[int, datetime]]) -> dict:
    """RF16: o primeiro erro corrigido depois da matrícula, quanto tempo levou e se
    veio ainda na sessão em que o aluno entrou na turma."""
    entrada = {m.aluno: m.entrada for m in matriculas}
    primeiro: dict[int, datetime] = {}
    for aluno, momento in corrigidos:
        if aluno in entrada and momento >= entrada[aluno]:
            if aluno not in primeiro or momento < primeiro[aluno]:
                primeiro[aluno] = momento

    eventos: dict[int, list[datetime]] = defaultdict(list)
    for t in tentativas:
        eventos[t.aluno].append(t.momento)
    for a in acessos:
        eventos[a.aluno].append(a.momento)

    minutos = []
    na_sessao = 0
    for aluno, momento in primeiro.items():
        minutos.append((momento - entrada[aluno]).total_seconds() / 60)
        if momento <= fim_da_sessao(entrada[aluno], eventos[aluno]):
            na_sessao += 1
    return {
        "chegaram": len(primeiro),
        "ainda_nao_chegaram": len(matriculas) - len(primeiro),
        "mediana_minutos": round(median(minutos), 1) if minutos else None,
        "na_sessao_da_matricula": na_sessao,
        "taxa_na_sessao_da_matricula": taxa(na_sessao, len(matriculas)),
    }


def montar_funil(dados: DadosDaTurma, alunos_previstos: int | None, agora: datetime) -> dict:
    corrigidos = erros_corrigidos(dados.tentativas)
    return {
        "north_star": north_star(corrigidos, agora),
        "aquisicao": aquisicao(dados.matriculas, alunos_previstos),
        "ativacao": ativacao(dados.matriculas, dados.tentativas, corrigidos),
        "retencao": retencao(dados.matriculas, dados.tentativas, dados.acessos, dados.janelas, agora),
        "saude": saude(dados.matriculas, dados.tentativas, dados.questoes_abertas, agora),
        "protecao": protecao(dados.tentativas),
        "sucesso": sucesso(dados.matriculas, dados.tentativas, dados.acessos, corrigidos),
    }
