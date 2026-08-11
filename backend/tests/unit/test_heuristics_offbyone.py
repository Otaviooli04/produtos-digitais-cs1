from app.engine.static_analyzer import extract_control_flow
from app.engine.heuristics import classify_error


def _risky(code):
    return extract_control_flow(code)["risky_loops"]


class TestDeteccaoOffByOne:
    def test_for_inclusivo_indexando_vetor(self):
        code = "int main(){ int a[10],i,n; for(i=0;i<=n;i++){ a[i]=i; } }"
        risky = _risky(code)
        assert len(risky) == 1
        assert risky[0]["var"] == "i"

    def test_for_com_menor_estrito_nao_e_risco(self):
        code = "int main(){ int a[10],i,n; for(i=0;i<n;i++){ a[i]=i; } }"
        assert _risky(code) == []

    def test_laco_reverso_nao_e_sinalizado(self):
        # for(i=n-1; i>=0; i--) é o padrão reverso correto — não deve disparar
        code = "int main(){ int a[10],i,n; for(i=n-1;i>=0;i--){ a[i]=i; } }"
        assert _risky(code) == []

    def test_inclusivo_sem_acesso_a_vetor_nao_dispara(self):
        # soma 1..n é uso legítimo de '<=' sem indexar vetor
        code = "int main(){ int i,n,soma=0; for(i=1;i<=n;i++){ soma+=i; } }"
        assert _risky(code) == []

    def test_while_inclusivo_indexando_vetor(self):
        code = "int main(){ int a[10],i=0,n; while(i<=n){ a[i]=0; i++; } }"
        risky = _risky(code)
        assert len(risky) == 1
        assert risky[0]["var"] == "i"

    def test_matriz_for_aninhado(self):
        # caso real (Prova-1 Q3): for(i=0;i<=m;i++) ... mat[i][j]
        code = "int main(){ int mat[5][5],i,j,m,n; for(i=0;i<=m;i++){ for(j=0;j<=n;j++){ mat[i][j]=0; } } }"
        risky = _risky(code)
        assert {r["var"] for r in risky} == {"i", "j"}

    def test_codigo_quebrado_ainda_detecta(self):
        # robustez: mesmo sem compilar (sem declarar n), o padrão é detectado
        code = "int main(){ int a[10],i; for(i=0;i<=n;i++) a[i]=i;"
        risky = _risky(code)
        assert len(risky) == 1


class TestHeuristicaOffByOne:
    def test_segfault_com_risco_vira_off_by_one(self):
        dyn = {"success": False, "compile_error": "Segmentation fault (core dumped)"}
        static = {"structures": ["For"], "risky_loops": [{"var": "i", "op": "<="}]}
        diag = classify_error(dyn, static)
        assert diag["error_category"] == "Acesso Fora dos Limites: Off-by-One"

    def test_segfault_sem_risco_mantem_categoria_generica(self):
        dyn = {"success": False, "compile_error": "Segmentation fault (core dumped)"}
        static = {"structures": [], "risky_loops": []}
        diag = classify_error(dyn, static)
        assert diag["error_category"] == "Acesso Indevido à Memória"

    def test_saida_incorreta_com_risco_adiciona_dica(self):
        dyn = {
            "success": True,
            "compile_error": "",
            "warnings": "",
            "all_tests_passed": False,
            "test_results": [
                {"input": "3", "expected_output": "0", "actual_output": "6", "passed": False}
            ],
        }
        static = {"structures": ["For"], "risky_loops": [{"var": "i", "op": "<="}]}
        diag = classify_error(dyn, static)
        assert diag["error_category"] == "Saída Incorreta"
        assert "off-by-one" in diag["actionable_feedback"].lower()

    def test_saida_incorreta_sem_risco_feedback_normal(self):
        dyn = {
            "success": True,
            "compile_error": "",
            "warnings": "",
            "all_tests_passed": False,
            "test_results": [
                {"input": "3", "expected_output": "0", "actual_output": "6", "passed": False}
            ],
        }
        static = {"structures": ["For"], "risky_loops": []}
        diag = classify_error(dyn, static)
        assert diag["error_category"] == "Saída Incorreta"
        assert "off-by-one" not in diag["actionable_feedback"].lower()
