import math
from dataclasses import dataclass


def check_structures(found: list, required: list, forbidden: list) -> dict:
    missing = [s for s in required if s not in found]
    prohibited = [s for s in forbidden if s in found]
    return {
        "compliant": len(missing) == 0 and len(prohibited) == 0,
        "missing_required": missing,
        "found_forbidden": prohibited,
    }


def _normalize_type(t: str) -> str:
    return "".join((t or "").split()).lower()


def check_functions(found: list, required: list) -> dict:
    found_by_name = {f["name"]: f for f in found}
    missing = []
    sig_mismatches = []
    missing_recursion = []
    missing_pointer = []

    for req in required:
        name = req.get("name")
        fn = found_by_name.get(name)
        if fn is None:
            missing.append(name)
            continue

        expected_count = req.get("param_count")
        if expected_count is not None and fn["param_count"] != expected_count:
            sig_mismatches.append(
                f"{name}: esperado {expected_count} parâmetro(s), encontrado {fn['param_count']}"
            )

        expected_return = req.get("return_type")
        if expected_return and _normalize_type(fn["return_type"]) != _normalize_type(expected_return):
            sig_mismatches.append(
                f"{name}: esperado retorno '{expected_return}', encontrado '{fn['return_type']}'"
            )

        if req.get("requires_recursion") and not fn["is_recursive"]:
            missing_recursion.append(name)

        if req.get("requires_pointer_param") and not fn["has_pointer_param"]:
            missing_pointer.append(name)

    compliant = not (missing or sig_mismatches or missing_recursion or missing_pointer)
    return {
        "compliant": compliant,
        "missing_functions": missing,
        "signature_mismatches": sig_mismatches,
        "missing_recursion": missing_recursion,
        "missing_pointer_param": missing_pointer,
    }


@dataclass
class DiagnosisContext:
    """Reúne os sinais de entrada que os verificadores consultam."""
    dyn_success: bool
    compile_error: str   # minúsculo
    warnings: str        # minúsculo
    structures: list
    functions: list
    risky_loops: list
    test_results: list
    required_structures: list
    forbidden_structures: list
    required_functions: list


def _build_context(
    dynamic_result: dict,
    static_result: dict,
    required_structures: list,
    forbidden_structures: list,
    required_functions: list,
) -> DiagnosisContext:
    return DiagnosisContext(
        dyn_success=dynamic_result.get("success", False),
        compile_error=dynamic_result.get("compile_error", "").lower(),
        warnings=dynamic_result.get("warnings", "").lower(),
        structures=static_result.get("structures", []),
        functions=static_result.get("functions", []),
        risky_loops=static_result.get("risky_loops", []),
        test_results=dynamic_result.get("test_results", []),
        required_structures=required_structures or [],
        forbidden_structures=forbidden_structures or [],
        required_functions=required_functions or [],
    )


# --- Verificadores: cada um retorna um diagnóstico ou None (não se aplica). ---
# A ordem da lista CHECKERS é a prioridade; o primeiro não-None vence.

def _check_compilation_error(ctx: DiagnosisContext) -> dict | None:
    if ctx.dyn_success or "error:" not in ctx.compile_error:
        return None
    return _classify_compilation_error(ctx.compile_error)


def _check_runtime_timeout(ctx: DiagnosisContext) -> dict | None:
    if ctx.dyn_success or "timeout" not in ctx.compile_error:
        return None
    return _classify_timeout(ctx.structures)


def _check_segfault(ctx: DiagnosisContext) -> dict | None:
    if ctx.dyn_success:
        return None
    if "segmentation fault" not in ctx.compile_error and "core dumped" not in ctx.compile_error:
        return None
    if ctx.risky_loops:
        return _classify_off_by_one(ctx.risky_loops, segfault=True)
    return {
        "error_category": "Acesso Indevido à Memória",
        "pedagogical_diagnosis": "O programa tentou acessar uma área de memória restrita (Segmentation Fault).",
        "actionable_feedback": "Verifique se os índices de vetores ultrapassam o limite declarado ou se há ponteiros não inicializados.",
    }


def _check_floating_point(ctx: DiagnosisContext) -> dict | None:
    if ctx.dyn_success or "floating point exception" not in ctx.compile_error:
        return None
    return {
        "error_category": "Erro Aritmético: Divisão por Zero",
        "pedagogical_diagnosis": "O programa executou uma divisão por zero em tempo de execução.",
        "actionable_feedback": "Adicione uma verificação para garantir que o divisor seja diferente de zero antes da operação.",
    }


def _check_warnings(ctx: DiagnosisContext) -> dict | None:
    if not ctx.dyn_success:
        return None
    return _classify_warnings(ctx.warnings)


def _check_structure_violation(ctx: DiagnosisContext) -> dict | None:
    if not ctx.dyn_success:
        return None
    struct_check = check_structures(ctx.structures, ctx.required_structures, ctx.forbidden_structures)
    if not struct_check["compliant"]:
        return _classify_structure_violation(struct_check)
    return None


def _check_function_violation(ctx: DiagnosisContext) -> dict | None:
    if not ctx.dyn_success or not ctx.required_functions:
        return None
    func_check = check_functions(ctx.functions, ctx.required_functions)
    if func_check["compliant"]:
        return None
    return _classify_function_violation(func_check, ctx.functions)


def _check_float_precision(ctx: DiagnosisContext) -> dict | None:
    """Saída com valores certos mas casas decimais erradas. Só dispara se todas as
    falhas forem puramente de precisão; senão deixa o checker de testes classificar."""
    if not ctx.dyn_success or not ctx.test_results:
        return None
    failed = [r for r in ctx.test_results if not r["passed"]]
    if not failed or any(r["actual_output"] == "TIMEOUT" for r in failed):
        return None
    mismatches = [_precision_mismatch(r["expected_output"], r["actual_output"]) for r in failed]
    if any(m is None for m in mismatches):
        return None
    exp_dec, got_dec = mismatches[0]
    return _classify_float_precision(exp_dec, got_dec)


def _check_tests(ctx: DiagnosisContext) -> dict | None:
    if not ctx.dyn_success or not ctx.test_results:
        return None
    failed = [r for r in ctx.test_results if not r["passed"]]
    if any(r["actual_output"] == "TIMEOUT" for r in failed):
        return _classify_timeout(ctx.structures)
    if failed:
        return _classify_wrong_output(failed, len(ctx.test_results), ctx.risky_loops)
    return {
        "error_category": "Correto",
        "pedagogical_diagnosis": f"Todos os {len(ctx.test_results)} testes passaram e as estruturas estão corretas.",
        "actionable_feedback": "Solução correta.",
    }


def _check_structural_fallback(ctx: DiagnosisContext) -> dict | None:
    if not ctx.dyn_success:
        return None
    return _classify_success(ctx.structures)


CHECKERS = [
    _check_compilation_error,
    _check_runtime_timeout,
    _check_segfault,
    _check_floating_point,
    _check_warnings,
    _check_structure_violation,
    _check_function_violation,
    _check_float_precision,
    _check_tests,
    _check_structural_fallback,
]

_UNKNOWN = {
    "error_category": "Erro Desconhecido",
    "pedagogical_diagnosis": "Ocorreu uma falha técnica não classificada pelas regras atuais.",
    "actionable_feedback": "Consulte os logs técnicos de execução.",
}


def classify_error(
    dynamic_result: dict,
    static_result: dict,
    required_structures: list = None,
    forbidden_structures: list = None,
    required_functions: list = None,
) -> dict:
    ctx = _build_context(
        dynamic_result, static_result,
        required_structures, forbidden_structures, required_functions,
    )
    for checker in CHECKERS:
        result = checker(ctx)
        if result is not None:
            return result
    return dict(_UNKNOWN)


def _classify_structure_violation(struct_check: dict) -> dict:
    parts = []
    if struct_check["missing_required"]:
        parts.append(f"estruturas obrigatórias não usadas: {struct_check['missing_required']}")
    if struct_check["found_forbidden"]:
        parts.append(f"estruturas proibidas encontradas: {struct_check['found_forbidden']}")
    return {
        "error_category": "Violação de Estrutura",
        "pedagogical_diagnosis": f"O código compilou, mas não respeita as restrições da questão: {'; '.join(parts)}.",
        "actionable_feedback": "Revise o enunciado: verifique quais estruturas de controle são exigidas ou proibidas.",
    }


def _classify_function_violation(func_check: dict, found_functions: list) -> dict | None:
    missing = func_check["missing_functions"]
    if missing:
        user_functions = [f["name"] for f in found_functions if f["name"] != "main"]
        if not user_functions:
            return {
                "error_category": "Tudo no Main",
                "pedagogical_diagnosis": (
                    f"O código resolve o problema inteiramente dentro do main, sem definir "
                    f"a(s) função(ões) exigida(s): {missing}."
                ),
                "actionable_feedback": (
                    "Modularize a solução: extraia a lógica para a(s) função(ões) pedida(s) no "
                    "enunciado, com o nome e a assinatura corretos."
                ),
            }
        return {
            "error_category": "Função Ausente",
            "pedagogical_diagnosis": f"A(s) função(ões) exigida(s) não foi(ram) definida(s): {missing}.",
            "actionable_feedback": "Implemente a(s) função(ões) com o nome exato indicado no enunciado.",
        }

    if func_check["signature_mismatches"]:
        return {
            "error_category": "Assinatura Incorreta",
            "pedagogical_diagnosis": (
                f"Função definida com assinatura diferente da exigida: "
                f"{'; '.join(func_check['signature_mismatches'])}."
            ),
            "actionable_feedback": (
                "Ajuste o número/tipo de parâmetros e o tipo de retorno conforme o enunciado."
            ),
        }

    if func_check["missing_recursion"]:
        return {
            "error_category": "Recursão Faltando",
            "pedagogical_diagnosis": (
                f"A(s) função(ões) {func_check['missing_recursion']} deveria(m) ser implementada(s) "
                f"de forma recursiva, mas não fazem chamada a si mesma(s)."
            ),
            "actionable_feedback": (
                "Reescreva a função para que ela chame a si mesma, com um caso base que encerra a recursão."
            ),
        }

    if func_check["missing_pointer_param"]:
        return {
            "error_category": "Por-Valor vs Por-Referência",
            "pedagogical_diagnosis": (
                f"A(s) função(ões) {func_check['missing_pointer_param']} deveria(m) receber parâmetro "
                f"por referência (ponteiro), mas usa(m) passagem por valor."
            ),
            "actionable_feedback": (
                "Declare o parâmetro como ponteiro (ex: int *x) e use o operador & na chamada para que "
                "a função altere o valor original."
            ),
        }

    return None


def _classify_wrong_output(failed: list, total: int, risky_loops: list = None) -> dict:
    exemplo = failed[0]
    feedback = "Revise a lógica do programa. Teste manualmente com as entradas indicadas e compare a saída esperada."
    if risky_loops:
        loop_vars = sorted({r["var"] for r in risky_loops})
        feedback += (
            f" Atenção: o laço com '<=' indexando vetor pela variável {loop_vars} pode acessar "
            "uma posição além do fim do vetor (off-by-one): verifique se deveria ser '<'."
        )
    return {
        "error_category": "Saída Incorreta",
        "pedagogical_diagnosis": (
            f"{len(failed)}/{total} testes falharam. "
            f"Exemplo: entrada '{exemplo['input']}' → esperado '{exemplo['expected_output']}', "
            f"obtido '{exemplo['actual_output']}'."
        ),
        "actionable_feedback": feedback,
    }


def _decimals(token: str) -> int | None:
    """Nº de casas decimais de um token numérico, ou None se não for número."""
    try:
        float(token)
    except ValueError:
        return None
    return len(token.split(".", 1)[1]) if "." in token else 0


def _precision_mismatch(expected: str, actual: str) -> tuple[int, int] | None:
    """(casas_esperadas, casas_encontradas) do 1º token que difere só em precisão;
    None se houver qualquer diferença de conteúdo/valor."""
    exp_toks, act_toks = expected.split(), actual.split()
    if len(exp_toks) != len(act_toks):
        return None
    diff = None
    for e, a in zip(exp_toks, act_toks):
        if e == a:
            continue
        de, da = _decimals(e), _decimals(a)
        if de is None or da is None:
            return None  # token não-numérico difere → não é só precisão
        if not math.isclose(float(e), float(a), rel_tol=1e-9, abs_tol=1e-9):
            return None  # valores diferentes → erro de lógica, não de formato
        if diff is None and de != da:
            diff = (de, da)
    return diff


def _classify_float_precision(expected_decimals: int, found_decimals: int) -> dict:
    return {
        "error_category": "Precisão de Saída: Casas Decimais",
        "pedagogical_diagnosis": (
            f"A saída tem os valores numéricos corretos, mas com número de casas "
            f"decimais diferente do esperado (esperado {expected_decimals}, "
            f"encontrado {found_decimals})."
        ),
        "actionable_feedback": (
            f"Ajuste o especificador de formato do printf para imprimir "
            f"{expected_decimals} casa(s) decimal(is) (ex.: \"%.{expected_decimals}f\")."
        ),
    }


def _classify_off_by_one(risky_loops: list, segfault: bool = False) -> dict:
    loop_vars = sorted({r["var"] for r in risky_loops})
    base = (
        f"O laço usa '<=' como limite e indexa um vetor com a variável {loop_vars}. "
        "Em C os índices válidos vão de 0 a tamanho-1, então '<=' costuma acessar uma "
        "posição além do fim do vetor (erro off-by-one)."
    )
    if segfault:
        base += " Esse acesso inválido provavelmente causou o Segmentation Fault."
    return {
        "error_category": "Acesso Fora dos Limites: Off-by-One",
        "pedagogical_diagnosis": base,
        "actionable_feedback": "Troque '<=' por '<' na condição do laço, ou aumente o tamanho do vetor declarado.",
    }


def _classify_compilation_error(message: str) -> dict:
    if "expected ';'" in message or 'expected ";"' in message:
        return {
            "error_category": "Sintaxe: Ponto e Vírgula Ausente",
            "pedagogical_diagnosis": "Uma ou mais instruções não foram terminadas com ';'.",
            "actionable_feedback": "Localize a linha indicada pelo compilador e adicione o ponto e vírgula ao final da instrução.",
        }

    if "undeclared" in message or "was not declared" in message:
        return {
            "error_category": "Sintaxe: Variável ou Função Não Declarada",
            "pedagogical_diagnosis": "O programa utiliza um identificador (variável ou função) que não foi declarado antes do uso.",
            "actionable_feedback": "Declare a variável antes de usá-la ou verifique se o nome está escrito corretamente.",
        }

    if "implicit declaration of function" in message:
        return {
            "error_category": "Sintaxe: Cabeçalho Faltando",
            "pedagogical_diagnosis": "Uma função da biblioteca padrão foi usada sem o #include correspondente (ex: printf sem #include <stdio.h>).",
            "actionable_feedback": "Adicione o #include adequado ao início do arquivo.",
        }

    if "undefined reference" in message:
        return {
            "error_category": "Linker: Função Indefinida",
            "pedagogical_diagnosis": "O compilador encontrou uma chamada de função que não tem implementação vinculada.",
            "actionable_feedback": "Verifique se a função foi implementada ou se falta algum #include de biblioteca.",
        }

    if "incompatible type" in message or "invalid conversion" in message:
        return {
            "error_category": "Semântica: Tipo Incompatível",
            "pedagogical_diagnosis": "Uma atribuição ou operação foi feita entre tipos de dados incompatíveis.",
            "actionable_feedback": "Verifique os tipos das variáveis envolvidas e aplique conversão explícita (cast) se necessário.",
        }

    if "control reaches end of non-void function" in message or "no return" in message:
        return {
            "error_category": "Semântica: Retorno Ausente",
            "pedagogical_diagnosis": "Uma função declarada com tipo de retorno não garante retornar um valor em todos os caminhos de execução.",
            "actionable_feedback": "Certifique-se de que a função possui um 'return' em todos os fluxos possíveis.",
        }

    return {
        "error_category": "Erro de Compilação",
        "pedagogical_diagnosis": "O código não compilou devido a um erro não classificado pelas regras atuais.",
        "actionable_feedback": "Leia a mensagem de erro do compilador com atenção para identificar a linha e o tipo do problema.",
    }


def _classify_timeout(structures: list) -> dict:
    loop_structures = {"While", "For", "DoWhile"}

    if any(s in structures for s in loop_structures):
        loops_found = [s for s in structures if s in loop_structures]
        return {
            "error_category": "Loop Infinito: Controle de Fluxo",
            "pedagogical_diagnosis": f"O programa entrou em loop infinito. Laços detectados: {loops_found}.",
            "actionable_feedback": "Verifique se a variável de parada do laço está sendo modificada corretamente dentro do bloco.",
        }

    return {
        "error_category": "Timeout Anômalo",
        "pedagogical_diagnosis": "O programa excedeu o tempo limite, mas nenhum laço de repetição foi detectado na AST.",
        "actionable_feedback": "Verifique se há recursão infinita ou se o programa aguarda uma entrada (scanf) que nunca chega.",
    }


def _classify_warnings(warnings: str) -> dict | None:
    if "uninitialized" in warnings or "may be uninitialized" in warnings:
        return {
            "error_category": "Aviso: Variável Não Inicializada",
            "pedagogical_diagnosis": "O código compilou, mas uma variável é lida antes de receber um valor definido. Isso causa comportamento imprevisível.",
            "actionable_feedback": "Inicialize todas as variáveis no momento da declaração (ex: int x = 0;).",
        }

    if "unused variable" in warnings:
        return {
            "error_category": "Aviso: Variável Declarada e Não Utilizada",
            "pedagogical_diagnosis": "O código declara uma variável que nunca é lida ou usada na lógica do programa.",
            "actionable_feedback": "Remova a variável ou verifique se esqueceu de usá-la na lógica do exercício.",
        }

    if "implicit declaration" in warnings:
        return {
            "error_category": "Aviso: Declaração Implícita de Função",
            "pedagogical_diagnosis": "Uma função foi chamada sem declaração prévia visível. O compilador assumiu um protótipo genérico, o que pode causar erros silenciosos.",
            "actionable_feedback": "Adicione o #include correto ou declare o protótipo da função antes de chamá-la.",
        }

    return None


def _classify_success(structures: list) -> dict:
    if not structures:
        return {
            "error_category": "Solução Sequencial: Sem Controle de Fluxo",
            "pedagogical_diagnosis": "O código compilou e executou, mas não utilizou nenhuma estrutura de controle de fluxo (if, for, while, switch).",
            "actionable_feedback": "Verifique se o enunciado exige alguma estrutura de decisão ou repetição que ainda não foi implementada.",
        }

    loop_count = sum(structures.count(s) for s in ["For", "While", "DoWhile"])
    if_count = structures.count("If")

    if if_count >= 4 and loop_count == 0:
        return {
            "error_category": "Estrutura Suspeita: Excesso de Condicionais",
            "pedagogical_diagnosis": f"O código usa {if_count} blocos 'if' sem nenhum laço de repetição. Isso pode indicar uma tentativa de simular repetição com condicionais encadeados.",
            "actionable_feedback": "Considere substituir os condicionais encadeados por uma estrutura de repetição (for ou while).",
        }

    return {
        "error_category": "Lógica Estrutural Válida",
        "pedagogical_diagnosis": f"Código compilou e executou. Estruturas utilizadas: {structures}.",
        "actionable_feedback": "A estrutura de controle está operacional. A próxima etapa avaliará a precisão da saída em relação ao enunciado.",
    }
