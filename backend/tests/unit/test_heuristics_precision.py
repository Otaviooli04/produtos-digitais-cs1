from app.engine.heuristics import classify_error, _precision_mismatch


def _dyn(expected, actual, passed=False):
    return {
        "success": True,
        "compile_error": "",
        "warnings": "",
        "all_tests_passed": passed,
        "test_results": [
            {"input": "x", "expected_output": expected, "actual_output": actual, "passed": passed}
        ],
    }


_STATIC = {"structures": ["For"], "risky_loops": [], "functions": []}


class TestPrecisionMismatch:
    def test_menos_casas_decimais(self):
        # esperado 3 casas (Q6), aluno imprimiu 2
        assert _precision_mismatch("412.690", "412.69") == (3, 2)

    def test_inteiro_vs_float_formatado(self):
        # esperado "10.00" (2 casas), aluno imprimiu "10"
        assert _precision_mismatch("10.00", "10") == (2, 0)

    def test_multivalor_so_precisao(self):
        assert _precision_mismatch("1.50 2.00", "1.5 2.0") == (2, 1)

    def test_valores_diferentes_nao_e_precisao(self):
        # mesma quantidade de casas, mas valor errado → None
        assert _precision_mismatch("9.90", "8.50") is None

    def test_token_nao_numerico_diferente_nao_e_precisao(self):
        assert _precision_mismatch("aprovado", "reprovado") is None

    def test_contagem_de_tokens_diferente(self):
        assert _precision_mismatch("1.0 2.0", "1.0") is None

    def test_iguais_retorna_none(self):
        # sem divergência de casas → None (não classifica como precisão)
        assert _precision_mismatch("3.14", "3.14") is None


class TestClassifyFloatPrecision:
    def test_classifica_precisao_decimal(self):
        diag = classify_error(_dyn("412.690", "412.69"), _STATIC)
        assert diag["error_category"] == "Precisão de Saída: Casas Decimais"
        assert "3" in diag["pedagogical_diagnosis"]
        assert "%.3f" in diag["actionable_feedback"]

    def test_valor_errado_continua_saida_incorreta(self):
        diag = classify_error(_dyn("9.90", "8.50"), _STATIC)
        assert diag["error_category"] == "Saída Incorreta"

    def test_se_um_teste_e_logica_nao_classifica_precisao(self):
        dyn = {
            "success": True, "compile_error": "", "warnings": "", "all_tests_passed": False,
            "test_results": [
                {"input": "a", "expected_output": "10.00", "actual_output": "10", "passed": False},
                {"input": "b", "expected_output": "5.00", "actual_output": "7.00", "passed": False},
            ],
        }
        diag = classify_error(dyn, _STATIC)
        assert diag["error_category"] == "Saída Incorreta"

    def test_todos_passando_continua_correto(self):
        diag = classify_error(_dyn("412.690", "412.690", passed=True), _STATIC)
        assert diag["error_category"] == "Correto"
