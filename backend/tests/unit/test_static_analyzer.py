from app.engine.static_analyzer import extract_control_flow


def _functions(code):
    result = extract_control_flow(code)
    assert result["success"], result.get("error")
    return {f["name"]: f for f in result["functions"]}


class TestDeteccaoDeFuncoes:
    def test_detecta_funcao_simples(self):
        code = "int soma(int a, int b) { return a + b; }"
        fns = _functions(code)
        assert "soma" in fns
        assert fns["soma"]["return_type"] == "int"
        assert fns["soma"]["param_count"] == 2
        assert fns["soma"]["returns_value"] is True

    def test_extrai_tipos_dos_parametros(self):
        code = "float media(int a, float b) { return b; }"
        params = _functions(code)["media"]["params"]
        assert [p["type"] for p in params] == ["int", "float"]

    def test_main_void_nao_conta_como_parametro(self):
        code = "int main(void) { return 0; }"
        assert _functions(code)["main"]["param_count"] == 0

    def test_main_sem_args_tem_zero_parametros(self):
        code = "int main() { return 0; }"
        assert _functions(code)["main"]["param_count"] == 0

    def test_funcao_void_sem_return_de_valor(self):
        code = "void imprime(int x) { x = x + 1; }"
        fn = _functions(code)["imprime"]
        assert fn["return_type"] == "void"
        assert fn["returns_value"] is False


class TestRecursao:
    def test_detecta_recursao_direta(self):
        code = "int fat(int n) { if (n <= 1) return 1; return n * fat(n - 1); }"
        assert _functions(code)["fat"]["is_recursive"] is True

    def test_funcao_iterativa_nao_e_recursiva(self):
        code = "int fat(int n) { int r = 1; for (int i = 2; i <= n; i++) r = r * i; return r; }"
        assert _functions(code)["fat"]["is_recursive"] is False


class TestPassagemPorReferencia:
    def test_detecta_parametro_ponteiro(self):
        code = "void troca(int *a, int *b) { int t = *a; *a = *b; *b = t; }"
        fn = _functions(code)["troca"]
        assert fn["has_pointer_param"] is True
        assert all(p["is_pointer"] for p in fn["params"])

    def test_vetor_como_parametro_conta_como_ponteiro(self):
        code = "int soma(int v[], int n) { return n; }"
        params = _functions(code)["soma"]["params"]
        assert params[0]["is_pointer"] is True
        assert params[1]["is_pointer"] is False

    def test_passagem_por_valor_nao_e_ponteiro(self):
        code = "void troca(int a, int b) { int t = a; a = b; b = t; }"
        assert _functions(code)["troca"]["has_pointer_param"] is False


class TestMultiplasFuncoes:
    def test_detecta_main_e_auxiliar(self):
        code = (
            "int dobro(int x) { return 2 * x; }\n"
            "int main() { return dobro(21); }"
        )
        fns = _functions(code)
        assert set(fns) == {"dobro", "main"}

    def test_tudo_no_main_so_define_main(self):
        code = "int main() { int x = 2 * 21; return 0; }"
        fns = _functions(code)
        assert list(fns) == ["main"]


class TestCompatibilidade:
    def test_estruturas_de_controle_continuam_funcionando(self):
        code = "int main() { if (1) { for (int i = 0; i < 3; i++) {} } return 0; }"
        result = extract_control_flow(code)
        assert result["success"] is True
        assert "If" in result["structures"]
        assert "For" in result["structures"]

    def test_codigo_quebrado_extrai_parcialmente(self):
        # Robustez: código que não compila ainda rende estruturas parciais.
        # Trecho real (Prova-1 T1): chaves trocadas, vírgula faltando no scanf.
        code = (
            "int main(){ int p,n,media,i; scanf(\"%d %d \", &p &n);"
            " while(p<n){ i++; } if(n==10){ printf(\"x\",n) }"
            " if(n==0) printf(\"y\",n); } else{ media=n+n/2; } return 0; }"
        )
        result = extract_control_flow(code)
        assert result["success"] is True
        assert result["parse_ok"] is False  # há nós de erro
        assert "While" in result["structures"]
        assert "If" in result["structures"]

    def test_codigo_valido_tem_parse_ok(self):
        result = extract_control_flow("int main() { return 0; }")
        assert result["success"] is True
        assert result["parse_ok"] is True
