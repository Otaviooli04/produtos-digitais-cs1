"""Relatório de esforço economizado na correção.

O argumento do produto para o professor é que ele revisa uma vez por dificuldade
em vez de uma vez por aluno. Este relatório mede isso na prova dele, com o dado
que já existe: quantas submissões chegaram e em quantos grupos de mesmo sintoma
elas colapsam.

O agrupamento aqui é o determinístico — categoria de erro + assinatura de falha —
e não depende do agrupamento com ML ter rodado.
"""
from app.ml.cluster import failure_signature
from app.models.orm import Exam
from app.services.exam_service import sorted_questions

# Estimativa de tempo de revisão manual por item. É parâmetro declarado, não
# medição: serve para converter a redução de itens em horas de forma transparente.
MINUTOS_POR_ITEM = 2


def build_effort_report(exam: Exam) -> dict:
    questoes = []
    total_submissoes = 0
    total_grupos = 0

    for question in sorted_questions(exam):
        submissoes = question.submissions
        grupos = {
            (s.error_category or "", failure_signature(s), bool(s.compile_error))
            for s in submissoes
        }
        total_submissoes += len(submissoes)
        total_grupos += len(grupos)
        questoes.append({
            "question_number": question.number,
            "submissoes": len(submissoes),
            "grupos": len(grupos),
            "fator_reducao": _fator(len(submissoes), len(grupos)),
        })

    minutos_economizados = max(0, total_submissoes - total_grupos) * MINUTOS_POR_ITEM
    return {
        "exam_id": exam.id,
        "filename": exam.filename or "",
        "total_submissoes": total_submissoes,
        "itens_a_revisar": total_grupos,
        "fator_reducao": _fator(total_submissoes, total_grupos),
        "minutos_por_item": MINUTOS_POR_ITEM,
        "minutos_economizados": minutos_economizados,
        "questoes": questoes,
    }


def _fator(submissoes: int, grupos: int) -> float | None:
    if not submissoes or not grupos:
        return None
    return round(submissoes / grupos, 1)
