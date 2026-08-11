"""
Testes de integração — usam Docker GCC e Gemini reais.
Rodar com: pytest tests/integration/ -v -m integration
"""
import io
import pytest
from unittest.mock import patch

from tests.conftest import fastapi_app, get_db, TestingSession
from app.auth.dependencies import get_current_professor
from app.models.orm import Professor, Turma

# ---------------------------------------------------------------------------
# Códigos C reais usados nos testes
# ---------------------------------------------------------------------------

CODE_PAR_IMPAR_CORRETO = """\
#include <stdio.h>
int main() {
    int n;
    scanf("%d", &n);
    if (n % 2 == 0)
        printf("par\\n");
    else
        printf("impar\\n");
    return 0;
}
"""

CODE_PAR_IMPAR_ERRADO = """\
#include <stdio.h>
int main() {
    printf("par\\n");
    return 0;
}
"""

CODE_COMPILE_ERROR = """\
#include <stdio.h>
int main() {
    int n
    scanf("%d", &n);
    return 0;
}
"""

# Usa math.h (sqrt com valor de runtime): exige linkar a libm (-lm). Serve de
# regressão para o fix do linker — sem -lm o gcc dá "undefined reference".
CODE_SQRT_MATH = """\
#include <stdio.h>
#include <math.h>
int main() {
    double x;
    scanf("%lf", &x);
    printf("%.2f\\n", sqrt(x));
    return 0;
}
"""

CODE_SOMA_CORRETO = """\
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\\n", a + b);
    return 0;
}
"""

CODE_SOMA_ERRADO_1 = """\
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\\n", a - b);
    return 0;
}
"""

CODE_SOMA_ERRADO_2 = """\
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\\n", a * b);
    return 0;
}
"""

# PDF mínimo válido para pymupdf (sem conteúdo — parse retorna string vazia)
MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
190
%%EOF"""

GEMINI_EXAM_STRUCTURE = """{
  "questions": [
    {
      "number": "1",
      "type": "code",
      "statement": "Escreva um programa em C que leia um número inteiro e imprima 'par' se for par ou 'impar' se for ímpar.",
      "required_structures": ["If"],
      "forbidden_structures": [],
      "requires_loop": false
    },
    {
      "number": "2",
      "type": "code",
      "statement": "Escreva um programa em C que leia dois inteiros e imprima a soma deles.",
      "required_structures": [],
      "forbidden_structures": [],
      "requires_loop": false
    }
  ]
}"""


# ---------------------------------------------------------------------------
# Fixtures de integração
# ---------------------------------------------------------------------------

@pytest.fixture()
def int_client():
    """Client com banco de teste real, sem mocks de dependências."""
    from fastapi.testclient import TestClient

    db = TestingSession()

    def override_get_db():
        yield db

    professor = Professor(email="prof@teste.com", nome="Professor Teste", senha_hash="x")
    db.add(professor)
    db.commit()
    db.refresh(professor)

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_current_professor] = lambda: professor
    with TestClient(fastapi_app) as c:
        yield c, db, professor
    fastapi_app.dependency_overrides.clear()
    db.rollback()
    from tests.conftest import Base, engine
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDockerGCC:
    def test_compilacao_e_execucao_real(self, int_client):
        client, db, professor = int_client

        # Cria prova e questão diretamente (sem chamar Gemini)
        from app.models.orm import Exam, Question, TestCase
        exam = Exam(filename="prova_integracao.pdf", raw_text="texto")
        db.add(exam)
        db.flush()
        q = Question(
            exam_id=exam.id,
            number="1",
            statement="Par ou ímpar",
            required_structures=["If"],
            forbidden_structures=[],
            requires_loop=False,
        )
        db.add(q)
        db.flush()
        db.add(TestCase(question_id=q.id, input="2", expected_output="par"))
        db.add(TestCase(question_id=q.id, input="3", expected_output="impar"))
        db.commit()

        resp = client.post("/submission/evaluate", json={
            "exam_id": exam.id,
            "question_number": "1",
            "code": CODE_PAR_IMPAR_CORRETO,
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["all_tests_passed"] is True
        assert data["compile_error"] == ""
        assert all(r["passed"] for r in data["test_results"])
        assert data["diagnosis"]["error_category"] == "Correto"

    def test_saida_incorreta_real(self, int_client):
        client, db, professor = int_client

        from app.models.orm import Exam, Question, TestCase
        exam = Exam(filename="prova.pdf", raw_text="texto")
        db.add(exam)
        db.flush()
        q = Question(exam_id=exam.id, number="1", statement="Par ou ímpar",
                     required_structures=[], forbidden_structures=[], requires_loop=False)
        db.add(q)
        db.flush()
        db.add(TestCase(question_id=q.id, input="3", expected_output="impar"))
        db.commit()

        resp = client.post("/submission/evaluate", json={
            "exam_id": exam.id,
            "question_number": "1",
            "code": CODE_PAR_IMPAR_ERRADO,
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["all_tests_passed"] is False
        assert data["diagnosis"]["error_category"] == "Saída Incorreta"

    def test_codigo_com_math_h_linka_libm(self, int_client):
        """Regressão do fix -lm: código de CS1 com sqrt/pow (math.h) deve compilar
        e passar — sem -lm o gcc reprova código correto com 'undefined reference'."""
        client, db, professor = int_client

        from app.models.orm import Exam, Question, TestCase
        exam = Exam(filename="prova.pdf", raw_text="texto")
        db.add(exam)
        db.flush()
        q = Question(exam_id=exam.id, number="1", statement="Raiz quadrada",
                     required_structures=[], forbidden_structures=[], requires_loop=False)
        db.add(q)
        db.flush()
        db.add(TestCase(question_id=q.id, input="16", expected_output="4.00"))
        db.add(TestCase(question_id=q.id, input="2", expected_output="1.41"))
        db.commit()

        resp = client.post("/submission/evaluate", json={
            "exam_id": exam.id,
            "question_number": "1",
            "code": CODE_SQRT_MATH,
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["compile_error"] == ""
        assert data["all_tests_passed"] is True

    def test_erro_de_compilacao_real(self, int_client):
        client, db, professor = int_client

        from app.models.orm import Exam, Question
        exam = Exam(filename="prova.pdf", raw_text="texto")
        db.add(exam)
        db.flush()
        q = Question(exam_id=exam.id, number="1", statement="Qualquer",
                     required_structures=[], forbidden_structures=[], requires_loop=False)
        db.add(q)
        db.commit()

        resp = client.post("/submission/evaluate", json={
            "exam_id": exam.id,
            "question_number": "1",
            "code": CODE_COMPILE_ERROR,
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["compile_error"] != ""
        assert data["all_tests_passed"] is None


@pytest.mark.integration
class TestGeminiReal:
    def test_upload_extrai_questoes_com_gemini_real(self, int_client):
        client, db, professor = int_client

        # A extração roda em segundo plano via thread; no teste, executamos o job
        # de forma síncrona na sessão de teste (a thread real usa o banco de produção).
        def run_sync(job_id, target):
            target(db, job_id)

        # Enviamos como DOCX para o extrator usar o texto mockado (caminho de
        # texto). Com PDF, a rota mandaria o arquivo nativo ao Gemini e o
        # MINIMAL_PDF (vazio) não tem questão a extrair.
        with patch("app.services.exam_service.parse_document", return_value=(
            "Questão 1: Escreva um programa em C que leia um número inteiro e "
            "imprima 'par' se for par ou 'impar' se for ímpar, usando if/else."
        )), patch("app.services.exam_service.run_in_background", side_effect=run_sync):
            resp = client.post(
                "/exam/upload",
                files={"file": ("prova.docx", b"docx-fake",
                                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )

        assert resp.status_code == 200
        exam_id = resp.json()["exam_id"]

        exam = client.get(f"/exam/{exam_id}").json()
        assert len(exam["questions"]) >= 1
        q = exam["questions"][0]
        assert q["number"] is not None
        assert len(q["statement"]) > 10

    def test_insights_com_gemini_real(self, int_client):
        client, db, professor = int_client

        from app.models.orm import Exam, Question, QuestionCluster, Submission
        from datetime import datetime, timezone

        turma = Turma(nome="Turma Teste", codigo="TT", professor_id=professor.id)
        db.add(turma)
        db.flush()
        exam = Exam(filename="prova.pdf", raw_text="texto", turma_id=turma.id)
        db.add(exam)
        db.flush()
        q = Question(
            exam_id=exam.id, number="1",
            statement="Escreva um programa que leia um número e diga se é par ou ímpar.",
            required_structures=["If"], forbidden_structures=[], requires_loop=False,
        )
        db.add(q)
        db.flush()

        sub = Submission(
            question_id=q.id,
            code=CODE_PAR_IMPAR_ERRADO,
            error_category="Saída Incorreta",
            pedagogical_diagnosis="",
            actionable_feedback="",
            all_tests_passed=False,
            ast_structures=[],
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(sub)
        db.flush()

        cluster = QuestionCluster(
            question_id=q.id,
            cluster_label=0,
            size=1,
            dominant_error="Saída Incorreta",
            representative_submission_id=sub.id,
        )
        db.add(cluster)
        db.commit()

        resp = client.post(f"/exam/{exam.id}/questions/1/insights")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["insights"]) == 1
        insight = data["insights"][0]
        assert len(insight["insight"]) > 20  # Gemini retornou texto real


@pytest.mark.integration
class TestFluxoCompleto:
    def test_end_to_end_submissao_clustering_insights(self, int_client):
        """
        Fluxo completo sem nenhum mock:
        1. Cria prova com 2 questões
        2. Adiciona test cases
        3. Submete 4 códigos com Docker real
        4. Roda clustering (UMAP + HDBSCAN reais)
        5. Gera insights com Gemini real
        """
        client, db, professor = int_client

        from app.models.orm import Exam, Question, TestCase, Submission
        from app.models.orm import QuestionCluster

        # 1. Cria prova
        turma = Turma(nome="Turma Teste", codigo="TT", professor_id=professor.id)
        db.add(turma)
        db.flush()
        exam = Exam(filename="prova_e2e.pdf", raw_text="texto", turma_id=turma.id)
        db.add(exam)
        db.flush()
        q = Question(
            exam_id=exam.id, number="2",
            statement="Leia dois inteiros e imprima a soma.",
            required_structures=[], forbidden_structures=[], requires_loop=False,
        )
        db.add(q)
        db.flush()

        # 2. Test cases
        db.add(TestCase(question_id=q.id, input="1 2", expected_output="3"))
        db.add(TestCase(question_id=q.id, input="10 5", expected_output="15"))
        db.commit()

        # 3. Submete 8 códigos com Docker real — 2 grupos distintos para o HDBSCAN
        codes = (
            [CODE_SOMA_CORRETO] * 4
            + [CODE_SOMA_ERRADO_1, CODE_SOMA_ERRADO_1,
               CODE_SOMA_ERRADO_2, CODE_SOMA_ERRADO_2]
        )
        for code in codes:
            resp = client.post("/submission/evaluate", json={
                "exam_id": exam.id,
                "question_number": "2",
                "code": code,
            })
            assert resp.status_code == 200

        subs = db.query(Submission).filter(Submission.question_id == q.id).all()
        assert len(subs) == 8

        # 4. Clustering com ML real
        resp = client.post(f"/exam/{exam.id}/questions/2/cluster")
        assert resp.status_code == 200
        cluster_data = resp.json()
        assert cluster_data["total_submissions"] == 8
        assert len(cluster_data["scatter"]) == 8

        db.expire_all()
        clusters_db = db.query(QuestionCluster).filter(
            QuestionCluster.question_id == q.id
        ).all()
        assert len(clusters_db) >= 1

        # 5. Insights com Gemini real
        resp = client.post(f"/exam/{exam.id}/questions/2/insights")
        assert resp.status_code == 200
        insights = resp.json()["insights"]
        assert len(insights) >= 1
        assert all(len(i["insight"]) > 10 for i in insights)


@pytest.mark.integration
class TestClusteringComDiversidade:
    """
    Testa o pipeline ML com 20 submissões distribuídas em 5 grupos
    estruturalmente distintos, simulando uma turma real.
    """

    # --- Grupo 1: solução correta (4 variantes com nomes de variáveis diferentes)
    CORRETO_1 = """\
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\\n", a + b);
    return 0;
}
"""
    CORRETO_2 = """\
#include <stdio.h>
int main() {
    int x, y;
    scanf("%d %d", &x, &y);
    int soma = x + y;
    printf("%d\\n", soma);
    return 0;
}
"""
    CORRETO_3 = """\
#include <stdio.h>
int main() {
    int num1, num2, resultado;
    scanf("%d %d", &num1, &num2);
    resultado = num1 + num2;
    printf("%d\\n", resultado);
    return 0;
}
"""
    CORRETO_4 = """\
#include <stdio.h>
int main() {
    int primeiro, segundo, total;
    scanf("%d %d", &primeiro, &segundo);
    total = primeiro + segundo;
    printf("%d\\n", total);
    return 0;
}
"""

    # --- Grupo 2: usa subtração em vez de soma (erro de operador)
    SUBTRACAO_1 = """\
#include <stdio.h>
int main() {
    int a, b;
    scanf("%d %d", &a, &b);
    printf("%d\\n", a - b);
    return 0;
}
"""
    SUBTRACAO_2 = """\
#include <stdio.h>
int main() {
    int x, y;
    scanf("%d %d", &x, &y);
    int diff = x - y;
    printf("%d\\n", diff);
    return 0;
}
"""
    SUBTRACAO_3 = """\
#include <stdio.h>
int main() {
    int num1, num2;
    scanf("%d %d", &num1, &num2);
    printf("%d\\n", num1 - num2);
    return 0;
}
"""
    SUBTRACAO_4 = """\
#include <stdio.h>
int main() {
    int p, q, diferenca;
    scanf("%d %d", &p, &q);
    diferenca = p - q;
    printf("%d\\n", diferenca);
    return 0;
}
"""

    # --- Grupo 3: ignora entrada, imprime valor fixo (não leu o enunciado)
    HARDCODED_1 = """\
#include <stdio.h>
int main() {
    printf("3\\n");
    return 0;
}
"""
    HARDCODED_2 = """\
#include <stdio.h>
int main() {
    printf("%d\\n", 3);
    return 0;
}
"""
    HARDCODED_3 = """\
#include <stdio.h>
int main() {
    int resultado = 3;
    printf("%d\\n", resultado);
    return 0;
}
"""
    HARDCODED_4 = """\
#include <stdio.h>
int main() {
    int soma = 10;
    printf("%d\\n", soma);
    return 0;
}
"""

    # --- Grupo 4: usa while para somar (lógica errada com loop)
    LOOP_1 = """\
#include <stdio.h>
int main() {
    int a, b, soma = 0;
    scanf("%d %d", &a, &b);
    while (a > 0) {
        soma++;
        a--;
    }
    printf("%d\\n", soma);
    return 0;
}
"""
    LOOP_2 = """\
#include <stdio.h>
int main() {
    int x, y, acc = 0, i;
    scanf("%d %d", &x, &y);
    for (i = 0; i < x; i++) {
        acc++;
    }
    printf("%d\\n", acc);
    return 0;
}
"""
    LOOP_3 = """\
#include <stdio.h>
int main() {
    int n1, n2, total = 0, k;
    scanf("%d %d", &n1, &n2);
    for (k = 0; k < n1; k++) total++;
    for (k = 0; k < n2; k++) total++;
    printf("%d\\n", total);
    return 0;
}
"""
    LOOP_4 = """\
#include <stdio.h>
int main() {
    int a, b, s = 0, j;
    scanf("%d %d", &a, &b);
    while (b > 0) { s += a; b--; }
    printf("%d\\n", s);
    return 0;
}
"""

    # --- Grupo 5: erro de compilação (ponto-e-vírgula faltando)
    COMPILE_ERR_1 = """\
#include <stdio.h>
int main() {
    int a, b
    scanf("%d %d", &a, &b);
    printf("%d\\n", a + b);
    return 0;
}
"""
    COMPILE_ERR_2 = """\
#include <stdio.h>
int main() {
    int x, y
    scanf("%d %d", &x, &y)
    printf("%d\\n", x + y);
    return 0;
}
"""
    COMPILE_ERR_3 = """\
#include <stdio.h>
int main() {
    int num1 num2;
    scanf("%d %d", &num1, &num2);
    printf("%d\\n", num1 + num2);
    return 0;
}
"""
    COMPILE_ERR_4 = """\
#include <stdio.h>
int main() {
    int p, q;
    scanf("%d %d", &p, &q)
    printf("%d\\n", p + q)
    return 0
}
"""

    def test_clustering_com_20_submissoes_diversas(self, int_client):
        client, db, professor = int_client

        from app.models.orm import Exam, Question, TestCase, Submission, QuestionCluster

        # Prova e questão
        turma = Turma(nome="Turma Teste", codigo="TT", professor_id=professor.id)
        db.add(turma)
        db.flush()
        exam = Exam(filename="prova_diversidade.pdf", raw_text="texto", turma_id=turma.id)
        db.add(exam)
        db.flush()
        q = Question(
            exam_id=exam.id, number="1",
            statement="Leia dois inteiros e imprima a soma.",
            required_structures=[], forbidden_structures=[], requires_loop=False,
        )
        db.add(q)
        db.flush()
        db.add(TestCase(question_id=q.id, input="1 2", expected_output="3"))
        db.add(TestCase(question_id=q.id, input="10 5", expected_output="15"))
        db.commit()

        # 20 submissões em 5 grupos de 4
        grupos = {
            "correto":       [self.CORRETO_1,      self.CORRETO_2,      self.CORRETO_3,      self.CORRETO_4],
            "subtracao":     [self.SUBTRACAO_1,    self.SUBTRACAO_2,    self.SUBTRACAO_3,    self.SUBTRACAO_4],
            "hardcoded":     [self.HARDCODED_1,    self.HARDCODED_2,    self.HARDCODED_3,    self.HARDCODED_4],
            "loop":          [self.LOOP_1,         self.LOOP_2,         self.LOOP_3,         self.LOOP_4],
            "compile_error": [self.COMPILE_ERR_1,  self.COMPILE_ERR_2,  self.COMPILE_ERR_3,  self.COMPILE_ERR_4],
        }

        resultados_por_grupo = {}
        for grupo, codes in grupos.items():
            resultados_por_grupo[grupo] = []
            for code in codes:
                resp = client.post("/submission/evaluate", json={
                    "exam_id": exam.id, "question_number": "1", "code": code,
                })
                assert resp.status_code == 200
                resultados_por_grupo[grupo].append(resp.json())

        total_subs = db.query(Submission).filter(Submission.question_id == q.id).count()
        assert total_subs == 20

        # Verifica diagnósticos por grupo antes do clustering
        for r in resultados_por_grupo["correto"]:
            assert r["all_tests_passed"] is True

        for r in resultados_por_grupo["subtracao"]:
            assert r["all_tests_passed"] is False

        for r in resultados_por_grupo["hardcoded"]:
            assert r["all_tests_passed"] is False

        for r in resultados_por_grupo["compile_error"]:
            assert r["compile_error"] != ""
            assert r["all_tests_passed"] is None

        # Clustering
        resp = client.post(f"/exam/{exam.id}/questions/1/cluster")
        assert resp.status_code == 200
        cluster_data = resp.json()

        assert cluster_data["total_submissions"] == 20
        assert len(cluster_data["scatter"]) == 20

        # Com 20 submissões em 5 grupos distintos o HDBSCAN deve encontrar >= 2 clusters
        assert len(cluster_data["clusters"]) >= 2

        # A maioria das submissões deve estar em algum cluster (não ser outlier)
        outliers = sum(1 for p in cluster_data["scatter"] if p["cluster_id"] == -1)
        assert outliers < 10, f"Muitos outliers: {outliers}/20"

        # Todos os pontos têm coordenadas 2D válidas
        for point in cluster_data["scatter"]:
            assert isinstance(point["x"], float)
            assert isinstance(point["y"], float)
