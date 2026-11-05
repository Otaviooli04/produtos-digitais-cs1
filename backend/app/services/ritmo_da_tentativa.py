"""Leitura do ritmo de envios de um aluno numa mesma questão ou exercício.

Duas regras, as duas sobre o que o banco já guarda: quanto a tentativa nova
avançou em relação à anterior (recompensa que vem do código do aluno) e quando
os envios viraram tentativa às cegas, que pede pausa antes de qualquer outra
recompensa (RF29).
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from itertools import pairwise

ENVIOS_PARA_PAUSA = 3
JANELA_DA_PAUSA = timedelta(minutes=5)
MUDANCA_MINIMA = 20
# Envios que o ritmo precisa olhar, com folga para falhas técnicas no meio.
JANELA_DO_RITMO = 6


@dataclass(frozen=True)
class EnvioDoRitmo:
    codigo: str
    quando: datetime | None
    passou: bool
    passados: int
    total: int
    # Falha técnica (Docker fora do ar, tempo esgotado do sistema) não é erro do
    # aluno, como no resto do histórico: não entra na pausa nem no avanço.
    falha: bool = False


def avanco(anterior: EnvioDoRitmo | None, atual: EnvioDoRitmo) -> dict | None:
    """Casos a mais (ou a menos) que na tentativa anterior.

    Só compara quando as duas rodaram o mesmo conjunto de casos. Erro de
    compilação roda zero casos, e "passou em 3 a mais" depois de consertar o
    ponto e vírgula seria verdade sem dizer nada sobre a lógica."""
    if anterior is None or anterior.passou or anterior.falha or atual.falha:
        return None
    if atual.total == 0 or anterior.total != atual.total:
        return None
    return {
        "casos_a_mais": atual.passados - anterior.passados,
        "passados": atual.passados,
        "passados_antes": anterior.passados,
        "total": atual.total,
    }


def _normalizado(codigo: str) -> str:
    return "\n".join(linha.strip() for linha in (codigo or "").splitlines() if linha.strip())


def tamanho_da_mudanca(antes: str, depois: str) -> int:
    """Caracteres trocados numa edição de um trecho só, ignorando espaço e linha em
    branco. Trocar um `<` por `<=` dá 1, reescrever o laço dá dezenas."""
    a, b = _normalizado(antes), _normalizado(depois)
    prefixo = 0
    limite = min(len(a), len(b))
    while prefixo < limite and a[prefixo] == b[prefixo]:
        prefixo += 1
    sufixo = 0
    while (sufixo < limite - prefixo
           and a[len(a) - 1 - sufixo] == b[len(b) - 1 - sufixo]):
        sufixo += 1
    return max(len(a), len(b)) - prefixo - sufixo


def sugerir_pausa(envios: list[EnvioDoRitmo]) -> bool:
    """Os últimos envios, em ordem de chegada, viraram tentativa às cegas?

    Três envios errados em até cinco minutos, com o mesmo número de casos certos
    e cada um quase igual ao anterior. Quem acerta não recebe pausa, quem
    avançou ou reescreveu o código está pensando, não chutando, e a falha do
    sistema fica de fora da conta."""
    validos = [e for e in envios if not e.falha]
    if len(validos) < ENVIOS_PARA_PAUSA:
        return False
    ultimos = validos[-ENVIOS_PARA_PAUSA:]
    if any(e.passou or e.quando is None for e in ultimos):
        return False
    if len({e.passados for e in ultimos}) > 1:
        return False
    if ultimos[-1].quando - ultimos[0].quando > JANELA_DA_PAUSA:
        return False
    return all(
        tamanho_da_mudanca(antes.codigo, depois.codigo) <= MUDANCA_MINIMA
        for antes, depois in pairwise(ultimos)
    )


def ritmo(envios: list[EnvioDoRitmo]) -> dict:
    """O que a tela do resultado mostra sobre o envio mais recente da lista.
    Quem chama pode passar só os últimos: `JANELA_DO_RITMO` envios bastam."""
    if not envios:
        return {"avanco": None, "sugerir_pausa": False}
    anterior = envios[-2] if len(envios) > 1 else None
    return {
        "avanco": avanco(anterior, envios[-1]),
        "sugerir_pausa": sugerir_pausa(envios),
    }
