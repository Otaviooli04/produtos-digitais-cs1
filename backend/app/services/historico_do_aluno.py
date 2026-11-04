"""Histórico do aluno: os envios das listas e as tentativas da trilha numa
lista só, em ordem de tempo.

O progresso, os erros recorrentes e a trilha leem daqui, então os três sempre
concordam sobre o que o aluno errou e o que ele já superou. As regras trabalham
sobre registros simples e se testam com listas montadas à mão. A classificação
de cada envio também mora aqui, e o funil da turma usa a mesma."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.services.calendario import semana_iso

CATEGORIA_CORRETA = "Correto"
# O que as heurísticas devolvem quando a execução falha por fora do código do
# aluno, como o Docker fora do ar. Não é erro dele.
CATEGORIA_FALHA_TECNICA = "Erro Desconhecido"

ACERTO = "acerto"
ERRO = "erro"
FALHA = "falha"

LISTA = "lista"
TRILHA = "trilha"

# Quantas tentativas válidas contam como "recentes" ao medir a tendência de um erro.
JANELA_RECENTE = 10
# Quantos lugares o painel mostra em "Aconteceu em".
ROTULOS_POR_ERRO = 5


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


# ── registros ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Envio:
    """Um envio do aluno, de lista ou de trilha, já classificado.

    `alvo` e `titulo` só existem na trilha: o erro para o qual o exercício foi
    feito e o nome dele."""
    origem: str
    item_id: int
    momento: datetime
    categoria: str
    resultado: str
    o_que_fazer: str = ""
    alvo: str = ""
    titulo: str = ""

    @property
    def item(self) -> tuple[str, int]:
        return (self.origem, self.item_id)


@dataclass(frozen=True)
class Erro:
    """Uma categoria que o aluno já errou, com as ocorrências em ordem de tempo."""
    categoria: str
    ocorrencias: tuple[Envio, ...]
    superado_em: datetime | None = None

    @property
    def ativo(self) -> bool:
        return self.superado_em is None

    @property
    def total(self) -> int:
        return len(self.ocorrencias)

    @property
    def no_treino(self) -> int:
        return sum(1 for e in self.ocorrencias if e.origem == TRILHA)

    @property
    def ultima_ocorrencia(self) -> datetime:
        return self.ocorrencias[-1].momento

    @property
    def o_que_fazer(self) -> str:
        return self.ocorrencias[-1].o_que_fazer


@dataclass(frozen=True)
class Tendencia:
    recentes: int
    anteriores: int
    sentido: str  # 'melhorando' | 'piorando' | 'estavel'


# ── erros ────────────────────────────────────────────────────────────────────

def erros_do_aluno(envios: list[Envio]) -> list[Erro]:
    """Cada categoria que o aluno errou: os ativos primeiro, pelo total e depois
    pelo nome, e os superados depois, do mais recente para o mais antigo.

    Superado é o erro em que, depois da última vez que ele apareceu, o aluno
    acertou um exercício da trilha feito para ele. Se o erro aparece de novo,
    volta a ser ativo até o próximo acerto. Falha técnica nunca vira erro."""
    por_categoria: dict[str, list[Envio]] = defaultdict(list)
    for e in envios:
        if e.resultado == ERRO:
            por_categoria[e.categoria].append(e)

    erros = []
    for categoria, ocorrencias in por_categoria.items():
        ultima = ocorrencias[-1].momento
        superado_em = next(
            (e.momento for e in envios
             if e.origem == TRILHA and e.alvo == categoria
             and e.resultado == ACERTO and e.momento > ultima),
            None,
        )
        erros.append(Erro(categoria, tuple(ocorrencias), superado_em))

    ativos = sorted((e for e in erros if e.ativo), key=lambda e: (-e.total, e.categoria))
    ja_superados = sorted(
        (e for e in erros if not e.ativo), key=lambda e: e.superado_em, reverse=True)
    return ativos + ja_superados


def superados(erros: list[Erro]) -> list[dict]:
    """Os erros superados no formato que o painel e a trilha mostram."""
    return [
        {"error_category": e.categoria, "total": e.total,
         "superado_em": e.superado_em.isoformat()}
        for e in erros if not e.ativo
    ]


def rotulos(erro: Erro, rotulo_da_questao: dict[int, str]) -> list[str]:
    """Onde o erro aconteceu, do mais recente para o mais antigo, sem repetir.
    A questão sem rótulo, de atividade que o aluno não vê, fica de fora."""
    vistos: list[str] = []
    for e in reversed(erro.ocorrencias):
        rotulo = (f"Trilha · {e.titulo}" if e.origem == TRILHA
                  else rotulo_da_questao.get(e.item_id))
        if rotulo and rotulo not in vistos:
            vistos.append(rotulo)
    return vistos[:ROTULOS_POR_ERRO]


def tendencias(envios: list[Envio]) -> dict[str, Tendencia]:
    """Para cada categoria errada, a frequência dela nas JANELA_RECENTE últimas
    tentativas válidas contra a do resto do histórico. A falha técnica não
    ocupa lugar em nenhuma das duas janelas."""
    validas = [e for e in envios if e.resultado != FALHA]
    janela = validas[-JANELA_RECENTE:]
    janela_anterior = len(validas) - len(janela)
    total = Counter(e.categoria for e in validas if e.resultado == ERRO)
    recentes = Counter(e.categoria for e in janela if e.resultado == ERRO)
    return {
        categoria: Tendencia(
            recentes[categoria],
            n - recentes[categoria],
            _sentido(recentes[categoria], n - recentes[categoria], len(janela), janela_anterior),
        )
        for categoria, n in total.items()
    }


def _sentido(recentes: int, anteriores: int, janela_recente: int, janela_anterior: int) -> str:
    """Sem histórico anterior suficiente não há tendência."""
    if janela_anterior == 0 or janela_recente == 0:
        return "estavel"
    taxa_recente = recentes / janela_recente
    taxa_anterior = anteriores / janela_anterior
    if taxa_recente <= taxa_anterior * 0.8:
        return "melhorando"
    if taxa_recente >= taxa_anterior * 1.2:
        return "piorando"
    return "estavel"


# ── progresso ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Resolucao:
    """O primeiro acerto de um item e quantas tentativas válidas ele levou,
    contando o próprio acerto."""
    item: tuple[str, int]
    momento: datetime
    tentativas: int


def resolucoes(envios: list[Envio]) -> list[Resolucao]:
    """Um registro por item resolvido. A falha técnica não conta como tentativa,
    e o que vem depois do primeiro acerto não muda nada."""
    validas: Counter[tuple[str, int]] = Counter()
    resolvidos: dict[tuple[str, int], Resolucao] = {}
    for e in envios:
        if e.item in resolvidos or e.resultado == FALHA:
            continue
        validas[e.item] += 1
        if e.resultado == ACERTO:
            resolvidos[e.item] = Resolucao(e.item, e.momento, validas[e.item])
    return list(resolvidos.values())


def dias_seguidos(envios: list[Envio], hoje: date) -> int:
    """Sequência de dias consecutivos com pelo menos um envio, terminando hoje ou
    ontem (quem enviou ontem ainda não perdeu a sequência)."""
    dias = {e.momento.date() for e in envios}
    referencia = hoje if hoje in dias else hoje - timedelta(days=1)
    sequencia = 0
    while referencia in dias:
        sequencia += 1
        referencia -= timedelta(days=1)
    return sequencia


def evolucao(envios: list[Envio], resolvidas: list[Resolucao]) -> list[dict]:
    """Série semanal de tentativas e de itens resolvidos pela primeira vez. Só
    aparecem as semanas com alguma tentativa."""
    tentativas = Counter(semana_iso(e.momento) for e in envios)
    primeiras = Counter(semana_iso(r.momento) for r in resolvidas)
    return [
        {"periodo": semana, "tentativas": tentativas[semana], "resolvidas": primeiras[semana]}
        for semana in sorted(tentativas)
    ]
