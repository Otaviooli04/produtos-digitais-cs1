"""A análise da turma diz o tipo de cada atividade, para a tela separar provas de listas."""
from app.models.orm import Exam, Question, Submission
from app.services.turma_service import get_turma_analytics


def test_cada_atividade_e_ponto_da_trajetoria_trazem_o_modo(db, exam_factory):
    prova = exam_factory(questions=[{"number": "1"}])
    lista = Exam(filename="lista.pdf", raw_text="", turma_id=prova.turma_id,
                 publicada=True, modo=Exam.MODO_TREINO)
    db.add(lista)
    db.flush()
    db.add(Question(exam_id=lista.id, number="1", statement="Enunciado"))
    db.commit()
    for exam in (prova, lista):
        db.refresh(exam)
        db.add(Submission(question_id=exam.questions[0].id, matricula="2026001",
                          code="int main(){}", error_category="Saída Incorreta"))
    db.commit()

    analise = get_turma_analytics(prova.turma_id, db)

    modos = {p["id"]: p["modo"] for p in analise["provas"]}
    assert modos == {prova.id: "prova", lista.id: "treino"}
    pontos = analise["trajetoria"][0]["pontos"]
    assert {p["modo"] for p in pontos} == {"prova", "treino"}
