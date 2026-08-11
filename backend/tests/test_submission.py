from unittest.mock import patch

from app.models.orm import Submission
from tests.conftest import make_subprocess_result


CODE_CORRETO = (
    '#include <stdio.h>\n'
    'int main(){\n'
    '    int n; scanf("%d",&n);\n'
    '    if(n%2==0) printf("par\\n");\n'
    '    else printf("impar\\n");\n'
    '    return 0;\n'
    '}'
)

CODE_ERRADO = (
    '#include <stdio.h>\n'
    'int main(){\n'
    '    printf("par\\n");\n'
    '    return 0;\n'
    '}'
)

CODE_COMPILE_ERROR = 'int main(){ int x = '


def _patch_docker(*run_results):
    return patch(
        "app.engine.dynamic_analyzer.subprocess.run",
        side_effect=list(run_results),
    )


class TestSubmissionEvaluate:
    def test_codigo_correto_passa_todos_testes(self, client, exam_factory, db):
        exam = exam_factory(questions=[{
            "number": "1",
            "required_structures": ["If"],
        }])
        q = exam.questions[0]
        db.add(__import__("app.models.orm", fromlist=["TestCase"]).TestCase(
            question_id=q.id, input="2", expected_output="par"
        ))
        db.add(__import__("app.models.orm", fromlist=["TestCase"]).TestCase(
            question_id=q.id, input="3", expected_output="impar"
        ))
        db.commit()

        compile_ok = make_subprocess_result(returncode=0)
        run_par = make_subprocess_result(stdout="par")
        run_impar = make_subprocess_result(stdout="impar")

        with _patch_docker(compile_ok, run_par, run_impar):
            resp = client.post("/submission/evaluate", json={
                "exam_id": exam.id,
                "question_number": "1",
                "code": CODE_CORRETO,
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["all_tests_passed"] is True
        assert all(r["passed"] for r in data["test_results"])

    def test_saida_errada_falha_teste(self, client, exam_factory, db):
        from app.models.orm import TestCase
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        db.add(TestCase(question_id=q.id, input="2", expected_output="par"))
        db.commit()

        compile_ok = make_subprocess_result(returncode=0)
        run_errado = make_subprocess_result(stdout="impar")

        with _patch_docker(compile_ok, run_errado):
            resp = client.post("/submission/evaluate", json={
                "exam_id": exam.id,
                "question_number": "1",
                "code": CODE_ERRADO,
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["all_tests_passed"] is False
        assert data["test_results"][0]["passed"] is False
        assert data["diagnosis"]["error_category"] == "Saída Incorreta"

    def test_erro_de_compilacao(self, client, exam_factory):
        exam = exam_factory(questions=[{"number": "1"}])

        compile_fail = make_subprocess_result(
            returncode=1,
            stderr="student_code.c:1:21: error: expected ';' before '}'"
        )

        with _patch_docker(compile_fail):
            resp = client.post("/submission/evaluate", json={
                "exam_id": exam.id,
                "question_number": "1",
                "code": CODE_COMPILE_ERROR,
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["compile_error"] != ""
        assert data["all_tests_passed"] is None
        assert "Sintaxe" in data["diagnosis"]["error_category"]

    def test_questao_inexistente_retorna_404(self, client, exam_factory):
        exam = exam_factory()
        compile_ok = make_subprocess_result(returncode=0)
        with _patch_docker(compile_ok):
            resp = client.post("/submission/evaluate", json={
                "exam_id": exam.id,
                "question_number": "99",
                "code": "int main(){}",
            })
        assert resp.status_code == 404

    def test_ast_structures_persistidas_na_submissao(self, client, exam_factory, db):
        from app.models.orm import TestCase
        exam = exam_factory(questions=[{"number": "1"}])
        q = exam.questions[0]
        db.add(TestCase(question_id=q.id, input="2", expected_output="par"))
        db.commit()

        compile_ok = make_subprocess_result(returncode=0)
        run_ok = make_subprocess_result(stdout="par")

        with _patch_docker(compile_ok, run_ok):
            resp = client.post("/submission/evaluate", json={
                "exam_id": exam.id,
                "question_number": "1",
                "code": CODE_CORRETO,
            })

        assert resp.status_code == 200
        sub = db.query(Submission).filter(Submission.question_id == q.id).first()
        assert sub is not None
        assert isinstance(sub.ast_structures, list)
        assert "If" in sub.ast_structures
