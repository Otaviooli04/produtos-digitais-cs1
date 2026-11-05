"""Novidades do aluno: o que chegou para ele e ele ainda não abriu.

São dois tipos: a resposta do professor ao grupo do erro do aluno e o exercício
da trilha que ficou pronto antes de ele pedir. Cada novidade guarda quando
chegou e quando foi vista, que é o dado do experimento 1 do Plano de Growth.

Este módulo é o único que grava e lê a tabela. A novidade é o registro em volta
do que a rota entrega, então falha aqui vai para o log e não derruba a rota."""
import logging
from datetime import datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.orm import ExercicioGerado, Novidade, Question, QuestionCluster, Submission

logger = logging.getLogger(__name__)

RETORNO = Novidade.TIPO_RETORNO
EXERCICIO = Novidade.TIPO_EXERCICIO


def _sem_derrubar(acao, o_que: str, db: Session) -> None:
    """O aluno precisa do diagnóstico e o professor da resposta salva. A
    novidade vem depois, e a falha dela fica no log."""
    try:
        acao()
    except Exception:  # noqa: BLE001, a novidade é secundária ao que a rota entrega
        logger.exception("Falha ao %s", o_que)
        db.rollback()


def _gravar(linhas: list[dict], db: Session) -> None:
    """Grava ignorando a repetida: o índice único parcial deixa uma só novidade
    não vista por aluno e origem."""
    if not linhas:
        return
    db.execute(insert(Novidade).values(linhas).on_conflict_do_nothing())
    db.commit()


def _alcancados(question_id: int, cluster_label: int, db: Session) -> list[int]:
    """Alunos com conta cuja tentativa mais recente na questão está no grupo.
    É a regra da tela da questão, que só mostra a resposta na mais recente."""
    envios = (
        db.query(Submission.student_id, Submission.cluster_id)
        .filter(Submission.question_id == question_id, Submission.student_id.isnot(None))
        .order_by(Submission.attempt_number, Submission.id)
        .all()
    )
    ultimo_grupo: dict[int, int | None] = {}
    for student_id, cluster_id in envios:
        ultimo_grupo[student_id] = cluster_id
    return [s for s, grupo in ultimo_grupo.items() if grupo == cluster_label]


def _registrar_resposta(grupo: QuestionCluster, db: Session, anterior: str | None) -> None:
    if anterior is not None and anterior == grupo.resposta_professor:
        return
    if not grupo.chave:
        return
    if not grupo.resposta_professor:
        db.query(Novidade).filter(
            Novidade.tipo == RETORNO,
            Novidade.question_id == grupo.question_id,
            Novidade.grupo_chave == grupo.chave,
            Novidade.vista_em.is_(None),
        ).delete(synchronize_session=False)
        db.commit()
        return
    questao = db.get(Question, grupo.question_id)
    if not questao or not questao.exam or not questao.exam.publicada:
        return
    _gravar([
        {"student_id": student_id, "tipo": RETORNO, "question_id": grupo.question_id,
         "grupo_chave": grupo.chave, "chegou_em": grupo.resposta_em or datetime.utcnow()}
        for student_id in _alcancados(grupo.question_id, grupo.cluster_label, db)
    ], db)


def registrar_resposta(grupo: QuestionCluster, db: Session, anterior: str | None = None) -> None:
    """Chamado depois de o professor salvar a resposta de um grupo.

    Com texto, cria a novidade de cada aluno alcançado. Quem ainda não viu a
    anterior fica com ela, e quem já viu ganha uma nova, porque o texto mudou.
    Sem texto, a resposta foi desfeita e as novidades não vistas dela somem.
    Se `anterior` vier e for igual ao texto atual, o professor só salvou de novo
    o mesmo texto e nada muda. Grupo sem `chave` é linha antiga, sem como
    ancorar a novidade."""
    _sem_derrubar(lambda: _registrar_resposta(grupo, db, anterior),
                  f"gravar as novidades do grupo {grupo.id}", db)


def registrar_exercicio(exercicio: ExercicioGerado, db: Session) -> None:
    """Chamado pela pré-geração da trilha. O exercício que o aluno pede e abre
    na hora não passa por aqui, porque não fica esperando por ele."""
    _sem_derrubar(lambda: _gravar([{
        "student_id": exercicio.student_id, "tipo": EXERCICIO, "exercicio_id": exercicio.id,
        "chegou_em": exercicio.created_at or datetime.utcnow(),
    }], db), f"gravar a novidade do exercício {exercicio.id}", db)


def _marcar(filtros: list, db: Session, agora: datetime | None) -> None:
    db.query(Novidade).filter(Novidade.vista_em.is_(None), *filtros).update(
        {Novidade.vista_em: agora or datetime.utcnow()}, synchronize_session=False)
    db.commit()


def marcar_resposta_vista(student_id: int, question_id: int, chave: str | None,
                          db: Session, agora: datetime | None = None) -> None:
    """A tela da questão entregou a resposta do grupo `chave`. Só a novidade
    desse grupo conta como vista."""
    if not chave:
        return
    _sem_derrubar(lambda: _marcar([
        Novidade.student_id == student_id,
        Novidade.tipo == RETORNO,
        Novidade.question_id == question_id,
        Novidade.grupo_chave == chave,
    ], db, agora), "marcar a resposta como vista", db)


def marcar_exercicio_visto(student_id: int, exercicio_id: int, db: Session,
                           agora: datetime | None = None) -> None:
    _sem_derrubar(lambda: _marcar([
        Novidade.student_id == student_id,
        Novidade.tipo == EXERCICIO,
        Novidade.exercicio_id == exercicio_id,
    ], db, agora), "marcar o exercício como visto", db)
