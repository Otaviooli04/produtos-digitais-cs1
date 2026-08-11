from app.engine.dynamic_analyzer import _normalize_ws


class TestNormalizeWhitespace:
    def test_colapsa_alinhamento_em_uma_linha(self):
        # programa imprime com %4d; esperado vem do PDF com 1 espaço
        assert _normalize_ws("   1    2    3") == _normalize_ws("1 2 3")

    def test_matriz_preserva_linhas(self):
        # Q3: matriz multi-linha, alinhada vs. junta — devem casar
        actual = "   1    2\n   3    4"
        expected = "1 2\n3 4"
        assert _normalize_ws(actual) == _normalize_ws(expected)

    def test_linhas_em_branco_nas_bordas_sao_removidas(self):
        assert _normalize_ws("\n\n1 2\n\n") == "1 2"

    def test_ordem_de_linhas_continua_exigida(self):
        # afrouxa só o espaçamento horizontal, não a estrutura
        assert _normalize_ws("1 2\n3 4") != _normalize_ws("3 4\n1 2")

    def test_numero_de_linhas_continua_exigido(self):
        assert _normalize_ws("1 2 3") != _normalize_ws("1\n2\n3")

    def test_tabs_e_espacos_misturados(self):
        assert _normalize_ws("1\t2  3") == _normalize_ws("1 2 3")
