"""Funil da turma calculado na hora, com o que o banco já guarda.

Este módulo só lê e converte em registros. As contas estão em `funil_regras`."""
from datetime import datetime
from app.core.tempo import agora_utc

from sqlalchemy.orm import Session, load_only

from app.models.orm import (
    Acesso as AcessoDoBanco, Enrollment, Exam, Professor, Question, Student, Submission,
    TentativaDeTreino, Turma,
)
from app.services.calendario import situacao_da_atividade
from app.services.funil_regras import (
    Acesso, DadosDaTurma, JanelaDeProva, Matricula, Tentativa,
    alunos_ativados, erros_corrigidos, janela_da_prova, montar_funil, north_star,
    retencao_da_semana, taxa, ultimas_semanas,
)
from app.services.historico_do_aluno import (
    LISTA, TRILHA, resultado_da_lista, resultado_da_trilha,
)

# Os sinais de hábito ficam fora do total: a prova é de uma turma e o total junta
# alunos de turmas diferentes.
_RETENCAO_NO_TOTAL = ("semana", "base", "voltaram", "taxa", "voltaram_por_envio", "taxa_por_envio")


def _matriculas(turma_id: int, db: Session) -> list[Matricula]:
    linhas = (
        db.query(Enrollment.student_id, Student.nome, Enrollment.created_at, Enrollment.origem)
        .join(Student, Student.id == Enrollment.student_id)
        .filter(Enrollment.turma_id == turma_id)
        .all()
    )
    return [Matricula(aluno=aluno, nome=nome, entrada=entrada, origem=origem)
            for aluno, nome, entrada, origem in linhas]


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
    """A trilha não tem turma, então o treino do aluno entra em todas as turmas
    dele, cada uma a partir da matrícula."""
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


def _acessos(alunos: list[int], db: Session) -> list[Acesso]:
    linhas = (
        db.query(AcessoDoBanco.student_id, AcessoDoBanco.momento, AcessoDoBanco.via)
        .filter(AcessoDoBanco.student_id.in_(alunos))
        .all()
    )
    return [Acesso(aluno=aluno, momento=momento, via=via) for aluno, momento, via in linhas]


def _janelas_das_provas(turma_id: int, db: Session) -> list[JanelaDeProva]:
    """Provas publicadas da turma com data. Atividade de treino não puxa ninguém."""
    linhas = (
        db.query(Exam.abre_em, Exam.fecha_em)
        .filter(Exam.turma_id == turma_id, Exam.publicada.is_(True),
                Exam.modo != Exam.MODO_TREINO)
        .all()
    )
    janelas = (janela_da_prova(abre_em, fecha_em) for abre_em, fecha_em in linhas)
    return [j for j in janelas if j is not None]


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


def _desde_a_matricula(registros: list, entrada: dict[int, datetime]) -> list:
    """Trilha e acesso não têm turma. Numa turma, só vale o que veio depois de o
    aluno entrar nela."""
    return [r for r in registros if r.momento >= entrada[r.aluno]]


def _dados_da_turma(turma: Turma, db: Session, agora: datetime) -> DadosDaTurma:
    matriculas = _matriculas(turma.id, db)
    entrada = {m.aluno: m.entrada for m in matriculas}
    alunos = list(entrada)
    tentativas: list[Tentativa] = []
    acessos: list[Acesso] = []
    if alunos:
        trilha = _desde_a_matricula(_tentativas_de_trilha(alunos, db), entrada)
        tentativas = _tentativas_de_lista(turma.id, alunos, db) + trilha
        acessos = _desde_a_matricula(_acessos(alunos, db), entrada)
    return DadosDaTurma(
        matriculas=matriculas,
        tentativas=tentativas,
        questoes_abertas=_questoes_abertas(turma.id, db, agora),
        acessos=acessos,
        janelas=_janelas_das_provas(turma.id, db),
    )


def funil_da_turma(turma: Turma, db: Session, agora: datetime | None = None) -> dict:
    agora = agora or agora_utc()
    dados = _dados_da_turma(turma, db, agora)
    return {
        "turma_id": turma.id,
        "gerado_em": agora.isoformat(),
        **montar_funil(dados, turma.alunos_previstos, agora),
    }


def funil_geral(db: Session, agora: datetime | None = None) -> dict:
    """Todas as turmas, para o script da equipe. O total conta cada item e cada
    aluno uma vez, então não é a soma das turmas: o treino de quem está em duas
    turmas aparece nas duas. Juntar o que cada turma leu faz cada aluno contar a
    partir da primeira matrícula."""
    agora = agora or agora_utc()
    turmas = db.query(Turma).order_by(Turma.id).all()
    professores = dict(db.query(Professor.id, Professor.nome).all())

    por_turma = []
    todas: set[Tentativa] = set()
    todos_os_acessos: set[Acesso] = set()
    primeira_entrada: dict[int, Matricula] = {}
    ativados: set[int] = set()
    for turma in turmas:
        dados = _dados_da_turma(turma, db, agora)
        funil = montar_funil(dados, turma.alunos_previstos, agora)
        todas.update(dados.tentativas)
        todos_os_acessos.update(dados.acessos)
        ativados |= alunos_ativados(dados.matriculas, erros_corrigidos(dados.tentativas))
        for m in dados.matriculas:
            atual = primeira_entrada.get(m.aluno)
            if atual is None or m.entrada < atual.entrada:
                primeira_entrada[m.aluno] = m
        semana_da_turma = funil["retencao"]["ultima_completa"]
        por_turma.append({
            "turma_id": turma.id,
            "nome": turma.nome,
            "professor": professores.get(turma.professor_id),
            "matriculados": funil["aquisicao"]["matriculados"],
            "alunos_previstos": turma.alunos_previstos,
            "por_origem": funil["aquisicao"]["por_origem"],
            "taxa_ativacao": funil["ativacao"]["taxa"],
            "taxa_retencao": semana_da_turma["taxa"],
            "taxa_retencao_envio": semana_da_turma["taxa_por_envio"],
            "taxa_sucesso_na_sessao": funil["sucesso"]["taxa_na_sessao_da_matricula"],
            "north_star_semana": funil["north_star"]["semana_atual"],
            "north_star_total": funil["north_star"]["total"],
            "vermelhos": len(funil["saude"]["vermelho"]),
        })

    matriculas = list(primeira_entrada.values())
    tentativas = list(todas)
    semana = retencao_da_semana(ultimas_semanas(agora)[-2], matriculas, tentativas,
                                list(todos_os_acessos), [])
    return {
        "gerado_em": agora.isoformat(),
        "total": {
            "north_star": north_star(erros_corrigidos(tentativas), agora),
            "professores_com_turma": len({t.professor_id for t in turmas if t.professor_id is not None}),
            "turmas_com_matricula": sum(1 for t in por_turma if t["matriculados"]),
            "matriculados": len(matriculas),
            "ativados": len(ativados),
            "taxa_ativacao": taxa(len(ativados), len(matriculas)),
            "retencao_ultima_semana": {chave: semana[chave] for chave in _RETENCAO_NO_TOTAL},
        },
        "por_turma": por_turma,
    }
