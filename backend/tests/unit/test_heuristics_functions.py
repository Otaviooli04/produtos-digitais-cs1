from app.engine.heuristics import check_functions, _classify_function_violation
from app.engine.static_analyzer import extract_control_flow


def _functions(code):
    result = extract_control_flow(code)
    assert result["success"], result.get("error")
    return result["functions"]


class TestCheckFunctions:
    def test_compliant_quando_tudo_bate(self):
        found = _functions("int soma(int a, int b) { return a + b; } int main() { return 0; }")
        required = [{"name": "soma", "param_count": 2, "return_type": "int"}]
        check = check_functions(found, required)
        assert check["compliant"] is True
        assert check["missing_functions"] == []

    def test_funcao_ausente(self):
        found = _functions("int main() { return 0; }")
        required = [{"name": "soma"}]
        check = check_functions(found, required)
        assert check["compliant"] is False
        assert check["missing_functions"] == ["soma"]

    def test_param_count_divergente(self):
        found = _functions("int soma(int a) { return a; } int main() { return 0; }")
        required = [{"name": "soma", "param_count": 2}]
        check = check_functions(found, required)
        assert check["compliant"] is False
        assert len(check["signature_mismatches"]) == 1
        assert "soma" in check["signature_mismatches"][0]

    def test_return_type_divergente(self):
        found = _functions("float soma(int a, int b) { return a; } int main() { return 0; }")
        required = [{"name": "soma", "return_type": "int"}]
        check = check_functions(found, required)
        assert check["compliant"] is False
        assert "retorno" in check["signature_mismatches"][0]

    def test_ponteiro_normaliza_espacos(self):
        found = _functions("void troca(int *a, int *b) { } int main() { return 0; }")
        required = [{"name": "troca", "return_type": "void"}]
        check = check_functions(found, required)
        assert check["compliant"] is True

    def test_recursao_faltando(self):
        found = _functions("int fat(int n) { return n; } int main() { return 0; }")
        required = [{"name": "fat", "requires_recursion": True}]
        check = check_functions(found, required)
        assert check["missing_recursion"] == ["fat"]

    def test_recursao_presente_satisfaz(self):
        found = _functions("int fat(int n) { if (n <= 1) return 1; return n * fat(n - 1); } int main() { return 0; }")
        required = [{"name": "fat", "requires_recursion": True}]
        check = check_functions(found, required)
        assert check["compliant"] is True

    def test_ponteiro_faltando(self):
        found = _functions("void inc(int x) { } int main() { return 0; }")
        required = [{"name": "inc", "requires_pointer_param": True}]
        check = check_functions(found, required)
        assert check["missing_pointer_param"] == ["inc"]

    def test_ponteiro_presente_satisfaz(self):
        found = _functions("void inc(int *x) { } int main() { return 0; }")
        required = [{"name": "inc", "requires_pointer_param": True}]
        check = check_functions(found, required)
        assert check["compliant"] is True


class TestClassifyFunctionViolation:
    def test_tudo_no_main_quando_so_existe_main(self):
        found = _functions("int main() { return 0; }")
        check = check_functions(found, [{"name": "soma"}])
        diag = _classify_function_violation(check, found)
        assert diag["error_category"] == "Tudo no Main"

    def test_funcao_ausente_quando_ha_outras_funcoes(self):
        found = _functions("int outra() { return 0; } int main() { return 0; }")
        check = check_functions(found, [{"name": "soma"}])
        diag = _classify_function_violation(check, found)
        assert diag["error_category"] == "Função Ausente"

    def test_assinatura_incorreta(self):
        found = _functions("int soma(int a) { return a; } int main() { return 0; }")
        check = check_functions(found, [{"name": "soma", "param_count": 2}])
        diag = _classify_function_violation(check, found)
        assert diag["error_category"] == "Assinatura Incorreta"

    def test_recursao_faltando(self):
        found = _functions("int fat(int n) { return n; } int main() { return 0; }")
        check = check_functions(found, [{"name": "fat", "requires_recursion": True}])
        diag = _classify_function_violation(check, found)
        assert diag["error_category"] == "Recursão Faltando"

    def test_por_valor_vs_referencia(self):
        found = _functions("void inc(int x) { } int main() { return 0; }")
        check = check_functions(found, [{"name": "inc", "requires_pointer_param": True}])
        diag = _classify_function_violation(check, found)
        assert diag["error_category"] == "Por-Valor vs Por-Referência"

    def test_compliant_retorna_none(self):
        found = _functions("int soma(int a, int b) { return a + b; } int main() { return 0; }")
        check = check_functions(found, [{"name": "soma", "param_count": 2}])
        diag = _classify_function_violation(check, found)
        assert diag is None
