"""Dica em etapas (2.3): colunas, gerador do Gemini, bloqueio da prova e rota."""
from app.models.orm import Submission


def _tentativa(db, exam_factory, categoria="Saída Incorreta"):
    exam = exam_factory(questions=[{"number": "1"}])
    sub = Submission(question_id=exam.questions[0].id, code="int main(){}",
                     error_category=categoria)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


class TestColunas:
    def test_tentativa_nasce_sem_ajuda(self, db, exam_factory):
        sub = _tentativa(db, exam_factory)
        assert sub.nivel_de_ajuda == 0
        assert sub.llm_pistas is None
        assert sub.ajuda_pedida_em is None

    def test_guarda_as_pistas(self, db, exam_factory):
        sub = _tentativa(db, exam_factory)
        sub.llm_pistas = ["Olhe a média.", "O cálculo na linha 3."]
        db.commit()
        sub_id = sub.id
        db.expunge(sub)  # força a leitura do banco, senão o atributo vive só no objeto
        sub = db.get(Submission, sub_id)
        assert sub.llm_pistas == ["Olhe a média.", "O cálculo na linha 3."]
