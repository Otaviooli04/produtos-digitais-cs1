"""Limite de requisições por janela deslizante, guardado em memória.

Vale enquanto o backend roda num processo só. Com vários processos, o contador
passa para um armazenamento comum (Redis) e as rotas continuam iguais.
"""
import math
import time
from collections import deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Depends, HTTPException, Request

from app.auth.dependencies import get_current_professor
from app.auth.student_dependencies import get_current_student
from app.models.orm import Professor, Student


@dataclass(frozen=True)
class Regra:
    nome: str
    maximo: int
    janela: int


LOGIN_POR_IP = Regra("login-ip", maximo=60, janela=60)
LOGIN_POR_EMAIL = Regra("login-email", maximo=10, janela=60)
CADASTRO = Regra("cadastro", maximo=30, janela=3600)
ENVIO_DO_ALUNO = Regra("envio-aluno", maximo=10, janela=60)
GEMINI_DO_ALUNO = Regra("gemini-aluno", maximo=10, janela=60)
CORRECAO_DO_PROFESSOR = Regra("correcao-professor", maximo=30, janela=60)
UPLOAD_DE_PROVA = Regra("upload-prova", maximo=10, janela=3600)
ENVIO_EM_LOTE = Regra("envio-em-lote", maximo=10, janela=3600)
INSIGHTS = Regra("insights", maximo=10, janela=3600)


class Limitador:
    def __init__(self, relogio=time.monotonic, varrer_acima_de: int = 10_000, teto: int = 100_000):
        self._relogio = relogio
        self._varrer_acima_de = varrer_acima_de
        self._teto = teto
        self._ultima_varredura = float("-inf")
        self._pedidos: dict[str, tuple[int, deque]] = {}
        self._trava = Lock()

    def espera(self, chave: str, regra: Regra) -> int:
        """Conta o pedido e devolve 0, ou devolve quantos segundos faltam sem contar."""
        agora = self._relogio()
        chave = f"{regra.nome}:{chave}"
        with self._trava:
            if len(self._pedidos) >= self._varrer_acima_de and agora - self._ultima_varredura >= 60:
                self._varrer(agora)
                self._ultima_varredura = agora
            if chave not in self._pedidos:
                # Sob uma enxurrada de chaves novas, a mais antiga sai primeiro
                # (o dicionário guarda a ordem de entrada).
                while len(self._pedidos) >= self._teto:
                    del self._pedidos[next(iter(self._pedidos))]
            _, fila = self._pedidos.setdefault(chave, (regra.janela, deque()))
            while fila and fila[0] <= agora - regra.janela:
                fila.popleft()
            if len(fila) >= regra.maximo:
                return max(1, math.ceil(fila[0] + regra.janela - agora))
            fila.append(agora)
            return 0

    def _varrer(self, agora: float) -> None:
        vencidas = [k for k, (janela, fila) in self._pedidos.items()
                    if not fila or fila[-1] <= agora - janela]
        for k in vencidas:
            del self._pedidos[k]

    def chaves(self) -> int:
        return len(self._pedidos)

    def limpar(self) -> None:
        with self._trava:
            self._pedidos.clear()


limitador = Limitador()


def mensagem_de_espera(segundos: int) -> str:
    if segundos < 60:
        quanto = f"{segundos} segundo" if segundos == 1 else f"{segundos} segundos"
    else:
        minutos = math.ceil(segundos / 60)
        quanto = f"{minutos} minuto" if minutos == 1 else f"{minutos} minutos"
    return f"Muitas tentativas seguidas. Espere {quanto} e tente de novo."


def conferir(chave: str, regra: Regra) -> None:
    segundos = limitador.espera(chave, regra)
    if segundos:
        raise HTTPException(
            status_code=429,
            detail=mensagem_de_espera(segundos),
            headers={"Retry-After": str(segundos)},
        )


def ip_de(request: Request) -> str:
    # Atrás de um proxy, isto é o IP do proxy até o uvicorn ler os cabeçalhos
    # encaminhados (--proxy-headers), o que entra junto com a hospedagem.
    return request.client.host if request.client else "desconhecido"


def conferir_login(request: Request, email: str) -> None:
    ip = ip_de(request)
    conferir(ip, LOGIN_POR_IP)
    conferir(f"{ip}:{email.strip().lower()[:254]}", LOGIN_POR_EMAIL)


def por_ip(regra: Regra):
    def dependencia(request: Request) -> None:
        conferir(ip_de(request), regra)
    dependencia.regra_do_limite = regra.nome
    return dependencia


def por_aluno(regra: Regra):
    def dependencia(current: Student = Depends(get_current_student)) -> None:
        conferir(f"aluno:{current.id}", regra)
    dependencia.regra_do_limite = regra.nome
    return dependencia


def por_professor(regra: Regra):
    def dependencia(professor: Professor = Depends(get_current_professor)) -> None:
        conferir(f"professor:{professor.id}", regra)
    dependencia.regra_do_limite = regra.nome
    return dependencia
