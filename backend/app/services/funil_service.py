"""Funil da turma calculado na hora, com o que o banco já guarda.

Este módulo só lê e converte em registros. As contas estão em `funil_regras`."""
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session, load_only

from app.models.orm import (
    Enrollment, Exam, Professor, Question, Student, Submission, TentativaDeTreino, Turma,
)
from app.services.calendario import situacao_da_atividade
from app.services.funil_regras import (
    LISTA, TRILHA, Matricula, Tentativa, alunos_ativados, erros_corrigidos, montar_funil,
    north_star, resultado_da_lista, resultado_da_trilha, retencao_da_semana, taxa,
    ultimas_semanas,
)


@dataclass
class _DadosDaTurma:
    matriculas: list[Matricula]
    tentativas: list[Tentativa]
    questoes_abertas: dict[int, int | None]


def _matriculas(turma_id: int, db: Session) -> list[Matricula]:
    linhas = (
        db.query(Enrollment.student_id, Student.nome, Enrollment.created_at)
        .join(Student, Student.id == Enrollment.student_id)
        .filter(Enrollment.turma_id == turma_id)
        .all()
    )
    return [Matricula(aluno=aluno, nome=nome, entrada=entrada) for aluno, nome, entrada in linhas]


def _tentativas_de_lista(turma_id: int, alunos: list[int], db: Session) -> list[Tentativa]:
    """Envios com conta, em atividade publicada da turma. Os do TCC, importados
    só com matrícula, ficam de fora."""
    linhas = (
        db.query(Submission.id, Submission.student_id, Submission.question_id,
                 Submission.submitted_at, Submission.error_category, Exam.modo)
        .join(Question, Question.id == Submission.question_id)
        .join(Exam, Exam.id == Question.exam_id)
        .filter(
            Exam.turma_id == turma_id,
            Exam.publicada.is_(True),
            Submission.student_id.in_(alunos),
            Submission.submitted_at.isnot(None),
        )
        .all()
    )
    return [
        Tentativa(aluno=aluno, origem=LISTA, item_id=questao, momento=momento, ordem=sid,
                  resultado=resultado_da_lista(categoria),
                  por_conta_propria=modo == Exam.MODO_TREINO)
        for sid, aluno, questao, momento, categoria, modo in linhas
    ]


def _tentativas_de_trilha(alunos: list[int], db: Session) -> list[Tentativa]:
    """A trilha não tem turma, então o treino do aluno entra em todas as turmas dele."""
    linhas = (
        db.query(TentativaDeTreino.id, TentativaDeTreino.student_id,
                 TentativaDeTreino.exercicio_id, TentativaDeTreino.submitted_at,
                 TentativaDeTreino.all_tests_passed, TentativaDeTreino.error_category)
        .filter(TentativaDeTreino.student_id.in_(alunos),
                TentativaDeTreino.submitted_at.isnot(None))
        .all()
    )
    return [
        Tentativa(aluno=aluno, origem=TRILHA, item_id=exercicio, momento=momento, ordem=tid,
                  resultado=resultado_da_trilha(passou, categoria), por_conta_propria=True)
        for tid, aluno, exercicio, momento, passou, categoria in linhas
    ]


def _questoes_abertas(turma_id: int, db: Session, agora: datetime) -> dict[int, int | None]:
    linhas = (
        db.query(Question.id, Exam)
        .join(Exam, Exam.id == Question.exam_id)
        .options(load_only(Exam.abre_em, Exam.fecha_em, Exam.max_tentativas))
        .filter(Exam.turma_id == turma_id, Exam.publicada.is_(True))
        .all()
    )
    return {
        questao: exam.max_tentativas for questao, exam in linhas
        if situacao_da_atividade(exam, agora) == "aberta"
    }


def _dados_da_turma(turma: Turma, db: Session, agora: datetime) -> _DadosDaTurma:
    matriculas = _matriculas(turma.id, db)
    alunos = [m.aluno for m in matriculas]
    tentativas: list[Tentativa] = []
    if alunos:
        tentativas = _tentativas_de_lista(turma.id, alunos, db) + _tentativas_de_trilha(alunos, db)
    return _DadosDaTurma(matriculas, tentativas, _questoes_abertas(turma.id, db, agora))


def funil_da_turma(turma: Turma, db: Session, agora: datetime | None = None) -> dict:
    agora = agora or datetime.utcnow()
    dados = _dados_da_turma(turma, db, agora)
    return {
        "turma_id": turma.id,
        "gerado_em": agora.isoformat(),
        **montar_funil(dados.matriculas, dados.tentativas, dados.questoes_abertas,
                       turma.alunos_previstos, agora),
    }


def funil_geral(db: Session, agora: datetime | None = None) -> dict:
    """Todas as turmas, para o script da equipe. O total conta cada item e cada
    aluno uma vez, então não é a soma das turmas: o treino de quem está em duas
    turmas aparece nas duas."""
    agora = agora or datetime.utcnow()
    turmas = db.query(Turma).order_by(Turma.id).all()
    professores = dict(db.query(Professor.id, Professor.nome).all())

    por_turma = []
    todas: set[Tentativa] = set()
    primeira_entrada: dict[int, Matricula] = {}
    ativados: set[int] = set()
    for turma in turmas:
        dados = _dados_da_turma(turma, db, agora)
        funil = montar_funil(dados.matriculas, dados.tentativas, dados.questoes_abertas,
                             turma.alunos_previstos, agora)
        todas.update(dados.tentativas)
        ativados |= alunos_ativados(dados.matriculas, erros_corrigidos(dados.tentativas))
        for m in dados.matriculas:
            atual = primeira_entrada.get(m.aluno)
            if atual is None or m.entrada < atual.entrada:
                primeira_entrada[m.aluno] = m
        por_turma.append({
            "turma_id": turma.id,
            "nome": turma.nome,
            "professor": professores.get(turma.professor_id),
            "matriculados": funil["aquisicao"]["matriculados"],
            "alunos_previstos": turma.alunos_previstos,
            "taxa_ativacao": funil["ativacao"]["taxa"],
            "taxa_retencao": funil["retencao"]["ultima_completa"]["taxa"],
            "north_star_semana": funil["north_star"]["semana_atual"],
            "north_star_total": funil["north_star"]["total"],
            "vermelhos": len(funil["saude"]["vermelho"]),
        })

    matriculas = list(primeira_entrada.values())
    tentativas = list(todas)
    return {
        "gerado_em": agora.isoformat(),
        "total": {
            "north_star": north_star(erros_corrigidos(tentativas), agora),
            "professores_com_turma": len({t.professor_id for t in turmas if t.professor_id is not None}),
            "turmas_com_matricula": sum(1 for t in por_turma if t["matriculados"]),
            "matriculados": len(matriculas),
            "ativados": len(ativados),
            "taxa_ativacao": taxa(len(ativados), len(matriculas)),
            "retencao_ultima_semana": retencao_da_semana(
                ultimas_semanas(agora)[-2], matriculas, tentativas),
        },
        "por_turma": por_turma,
    }
