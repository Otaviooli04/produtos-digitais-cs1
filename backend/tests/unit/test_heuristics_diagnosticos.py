from app.engine.heuristics import classify_error

_STATIC = {"structures": [], "risky_loops": [], "functions": []}

PONTO_E_VIRGULA = "Sintaxe: Ponto e Vírgula Ausente"
DIVISAO_INTEIRA = "Erro Aritmético: Divisão Inteira"


def _compilacao(mensagem):
    return {"success": False, "compile_error": mensagem, "warnings": "", "test_results": []}


def _saidas(*pares):
    return {
        "success": True, "compile_error": "", "warnings": "", "all_tests_passed": False,
        "test_results": [
            {"input": str(i), "expected_output": esperado, "actual_output": obtido,
             "passed": esperado == obtido}
            for i, (esperado, obtido) in enumerate(pares)
        ],
    }


class TestPontoEVirgulaAusente:
    """Mensagens copiadas do gcc da imagem fixa, que vem antes do "undeclared"
    em cascata."""

    def test_declaracao_sem_ponto_e_virgula_antes_de_atribuicao(self):
        msg = ("/tmp/main.c:4:5: error: expected '=', ',', ';', 'asm' or '__attribute__' "
               "before 'x'\n/tmp/main.c:4:5: error: 'x' undeclared (first use in this function)")
        assert classify_error(_compilacao(msg), _STATIC)["error_category"] == PONTO_E_VIRGULA

    def test_lista_de_declaracao_sem_ponto_e_virgula(self):
        msg = "/tmp/main.c:4:5: error: expected ',' or ';' before 'scanf'"
        assert classify_error(_compilacao(msg), _STATIC)["error_category"] == PONTO_E_VIRGULA

    def test_forma_simples_continua_reconhecida(self):
        msg = ("/tmp/main.c:3:10: error: expected ';' before 'int'\n"
               "/tmp/main.c:5:5: error: 'x' undeclared (first use in this function)")
        assert classify_error(_compilacao(msg), _STATIC)["error_category"] == PONTO_E_VIRGULA

    def test_ponto_e_virgula_depois_do_before_nao_conta(self):
        msg = "/tmp/main.c:4:14: error: expected ')' before ';' token"
        assert classify_error(_compilacao(msg), _STATIC)["error_category"] != PONTO_E_VIRGULA

    def test_variavel_realmente_nao_declarada_continua_assim(self):
        msg = "/tmp/main.c:5:5: error: 'total' undeclared (first use in this function)"
        diag = classify_error(_compilacao(msg), _STATIC)
        assert diag["error_category"] == "Sintaxe: Variável ou Função Não Declarada"


class TestDivisaoInteira:
    def test_media_com_casas_decimais_truncada(self):
        diag = classify_error(_saidas(("2.50", "2.00"), ("3.00", "3.00")), _STATIC)
        assert diag["error_category"] == DIVISAO_INTEIRA
        assert "esperado '2.50'" in diag["pedagogical_diagnosis"]
        assert "obtido '2.00'" in diag["pedagogical_diagnosis"]
        assert "2.0" in diag["actionable_feedback"]

    def test_impresso_como_inteiro(self):
        diag = classify_error(_saidas(("2.5", "2")), _STATIC)
        assert diag["error_category"] == DIVISAO_INTEIRA

    def test_negativo_trunca_em_direcao_ao_zero(self):
        diag = classify_error(_saidas(("-2.50", "-2.00")), _STATIC)
        assert diag["error_category"] == DIVISAO_INTEIRA

    def test_texto_ao_redor_igual(self):
        diag = classify_error(_saidas(("Media: 7.50", "Media: 7.00")), _STATIC)
        assert diag["error_category"] == DIVISAO_INTEIRA

    def test_valor_errado_sem_truncamento_continua_saida_incorreta(self):
        diag = classify_error(_saidas(("2.50", "3.00")), _STATIC)
        assert diag["error_category"] == "Saída Incorreta"

    def test_um_caso_de_logica_derruba_a_divisao_inteira(self):
        diag = classify_error(_saidas(("2.50", "2.00"), ("4.00", "9.00")), _STATIC)
        assert diag["error_category"] == "Saída Incorreta"

    def test_esperado_inteiro_nao_e_divisao_inteira(self):
        diag = classify_error(_saidas(("3", "2")), _STATIC)
        assert diag["error_category"] == "Saída Incorreta"

    def test_so_casas_decimais_continua_precisao(self):
        diag = classify_error(_saidas(("10.00", "10")), _STATIC)
        assert diag["error_category"] == "Precisão de Saída: Casas Decimais"

    def test_nan_e_inf_nao_derrubam_a_classificacao(self):
        for esperado, obtido in [("nan", "0"), ("inf", "2"), ("2.50", "inf"), ("2.50", "nan")]:
            diag = classify_error(_saidas((esperado, obtido)), _STATIC)
            assert diag["error_category"] == "Saída Incorreta"

    def test_meio_negativo_trunca_para_zero(self):
        diag = classify_error(_saidas(("-0.50", "0.00")), _STATIC)
        assert diag["error_category"] == DIVISAO_INTEIRA

    def test_texto_diferente_nao_e_divisao_inteira(self):
        diag = classify_error(_saidas(("Media: 7.50", "media 7.00")), _STATIC)
        assert diag["error_category"] == "Saída Incorreta"
