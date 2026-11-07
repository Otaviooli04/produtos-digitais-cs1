"""Início do aluno: o que chegou para ele, onde ele parou e o que vence logo.

Monta o painel e não grava nada na sessão dele. A única escrita que ele dispara
é o exercício da prova chegando, preparado em thread própria. As novidades vêm
do `novidades_service`, e o resto sai do histórico unificado (`ler_historico`),
o mesmo do progresso e da trilha, para os três concordarem sobre o que está
resolvido. A regra mora em funções puras sobre registros simples, testadas sem
banco."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from app.core.tempo import agora_utc

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.orm import Exam, ExercicioGerado, Student, Submission
from app.services.calendario import situacao_da_atividade
from app.services.funil_regras import ANTECEDENCIA_DA_PROVA
from app.services.historico_do_aluno import (
    ACERTO, FALHA, LISTA, TRILHA, Envio, erros_do_aluno, ler_historico,
)
from app.services.novidades_service import novidades_do_aluno
from app.services.prova_chegando import montar_cartao, primeiro_pendente, prova_na_janela
from app.services.student_activity_service import titulo_da_atividade
from app.services.treino_service import preparar_proximo


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


def painel(student: Student, db: Session, agora: datetime | None = None) -> dict:
    """O Início do aluno. Sem matrícula, só avisa que ele não tem turma."""
    agora = agora or agora_utc()
    turma_ids = [e.turma_id for e in student.enrollments]
    if not turma_ids:
        return {"tem_turma": False, "novidades": [], "prova_chegando": None, "continuar": None,
                "prazos": []}

    envios = ler_historico(student, db)
    atividades, disponiveis = _atividades_e_questoes(student, turma_ids, envios, agora, db)
    disponiveis.update(_exercicios_abertos(student, db))
    prazos = prazos_proximos(atividades, agora)
    cartao = _prova_chegando(student, atividades, envios, agora)
    if cartao:
        prazos = [p for p in prazos if p["exam_id"] != cartao["exam_id"]]
    return {
        "tem_turma": True,
        "novidades": novidades_do_aluno(student, db),
        "prova_chegando": cartao,
        "continuar": escolher_continuar(envios, disponiveis, proxima_atividade(atividades)),
        "prazos": prazos,
    }


def _prova_chegando(student: Student, atividades: list[AtividadeDoPainel], envios: list[Envio],
                    agora: datetime) -> dict | None:
    """O cartão da prova chegando, com o exercício do primeiro erro pendente já a
    caminho, sem novidade, porque o aluno está vendo o treino no próprio cartão."""
    atividade = prova_na_janela(atividades, agora)
    if not atividade:
        return None
    cartao = montar_cartao(atividade, erros_do_aluno(envios), envios)
    if cartao:
        pendente = primeiro_pendente(cartao)
        if pendente:
            preparar_proximo(student.id, pendente, registrar_novidade=False)
    return cartao


def _atividades_e_questoes(student: Student, turma_ids: list[int], envios: list[Envio],
                           agora: datetime, db: Session):
    """As atividades publicadas das turmas do aluno e, das abertas, as questões
    sem acerto que ainda têm tentativa. O teto conta todos os envios da questão,
    como o `submeter` conta."""
    resolvidas = {e.item_id for e in envios if e.origem == LISTA and e.resultado == ACERTO}
    usadas = dict(
        db.query(Submission.question_id, func.count(Submission.id))
        .filter(Submission.student_id == student.id)
        .group_by(Submission.question_id)
        .all()
    )
    exams = (
        db.query(Exam)
        .filter(Exam.turma_id.in_(turma_ids), Exam.publicada.is_(True))
        .all()
    )
    atividades: list[AtividadeDoPainel] = []
    disponiveis: dict[tuple[str, int], ItemDisponivel] = {}
    for exam in exams:
        situacao = situacao_da_atividade(exam, agora)
        titulo = titulo_da_atividade(exam)
        turma_nome = exam.turma.nome if exam.turma else ""
        pendentes = [
            q for q in exam.questions
            if q.id not in resolvidas
            and (exam.max_tentativas is None or usadas.get(q.id, 0) < exam.max_tentativas)
        ]
        atividades.append(AtividadeDoPainel(
            exam_id=exam.id, titulo=titulo, turma_nome=turma_nome,
            modo=exam.modo or Exam.MODO_PROVA, situacao=situacao,
            abre_em=exam.abre_em, fecha_em=exam.fecha_em, criada_em=exam.created_at,
            com_o_que_fazer=bool(pendentes),
        ))
        if situacao == "aberta":
            for q in pendentes:
                disponiveis[(LISTA, q.id)] = ItemDisponivel(
                    origem=LISTA, item_id=q.id, titulo=f"Questão {q.number} · {titulo}",
                    turma_nome=turma_nome, exam_id=exam.id, question_number=q.number)
    return atividades, disponiveis


def _exercicios_abertos(student: Student, db: Session) -> dict[tuple[str, int], ItemDisponivel]:
    abertos = (
        db.query(ExercicioGerado)
        .filter(ExercicioGerado.student_id == student.id,
                ExercicioGerado.resolvido.is_(False),
                ExercicioGerado.reportado.is_(False))
        .all()
    )
    return {
        (TRILHA, e.id): ItemDisponivel(origem=TRILHA, item_id=e.id, titulo=e.titulo,
                                       exercicio_id=e.id)
        for e in abertos
    }
