"""Análise estática de C com tree-sitter, tolerante a erros de sintaxe.

`extract_control_flow` retorna {"success", "structures", "functions", "risky_loops",
"parse_ok"}; parse_ok=False quando a árvore tem nós de erro, mas structures/functions
ainda trazem o que foi extraído."""

from __future__ import annotations

import tree_sitter_c
from tree_sitter import Language, Node, Parser

_C_LANGUAGE = Language(tree_sitter_c.language())
_parser = Parser(_C_LANGUAGE)

_STRUCT_MAP = {
    "if_statement": "If",
    "for_statement": "For",
    "while_statement": "While",
    "do_statement": "DoWhile",
    "switch_statement": "Switch",
}


def extract_control_flow(source_code: str) -> dict:
    try:
        tree = _parser.parse(bytes(source_code, "utf8"))
        root = tree.root_node

        structures: list[str] = []
        functions: list[dict] = []
        risky_loops: list[dict] = []
        for node in _walk(root):
            label = _STRUCT_MAP.get(node.type)
            if label is not None:
                structures.append(label)
            elif node.type == "function_definition":
                fn = _extract_function(node)
                if fn is not None:
                    functions.append(fn)

            if node.type in ("for_statement", "while_statement"):
                risky = _risky_loop(node)
                if risky is not None:
                    risky_loops.append(risky)

        return {
            "success": True,
            "structures": structures,
            "functions": functions,
            "risky_loops": risky_loops,
            "parse_ok": not root.has_error,
        }
    except Exception as e:  # noqa: BLE001 — rede de segurança; tree-sitter raramente lança
        return {"success": False, "error": f"Erro de parsing na AST: {str(e)}"}


def _walk(node: Node):
    """Percurso em pré-ordem (ordem de documento)."""
    yield node
    for child in node.children:
        yield from _walk(child)


def _text(node: Node | None) -> str:
    return node.text.decode("utf8") if node is not None else ""


def _unwrap_declarator(decl: Node | None) -> tuple[Node | None, int]:
    """Desce por pointer_declarator até o function_declarator. Retorna (func_decl, nível_ponteiro)."""
    depth = 0
    cur = decl
    while cur is not None and cur.type == "pointer_declarator":
        depth += 1
        cur = cur.child_by_field_name("declarator")
    if cur is not None and cur.type == "function_declarator":
        return cur, depth
    return None, depth


def _extract_function(node: Node) -> dict | None:
    func_decl, ptr_depth = _unwrap_declarator(node.child_by_field_name("declarator"))
    if func_decl is None:
        return None

    name_node = func_decl.child_by_field_name("declarator")
    if name_node is None or name_node.type != "identifier":
        return None
    name = _text(name_node)

    return_type = _text(node.child_by_field_name("type"))
    if ptr_depth:
        return_type = f"{return_type} {'*' * ptr_depth}".strip()

    params = _extract_params(func_decl.child_by_field_name("parameters"))
    body = node.child_by_field_name("body")

    return {
        "name": name,
        "return_type": return_type,
        "params": params,
        "param_count": len(params),
        "is_recursive": _is_recursive(body, name),
        "has_pointer_param": any(p["is_pointer"] for p in params),
        "returns_value": _returns_value(body),
    }


def _extract_params(param_list: Node | None) -> list:
    if param_list is None:
        return []
    params = []
    for pd in param_list.named_children:
        if pd.type == "variadic_parameter":
            params.append({"name": "...", "type": "...", "is_pointer": False})
            continue
        if pd.type != "parameter_declaration":
            continue

        type_text = _text(pd.child_by_field_name("type"))
        declarator = pd.child_by_field_name("declarator")

        # `void` sem nome (ex: int main(void)) não conta como parâmetro real
        if declarator is None and type_text == "void":
            continue

        is_pointer = declarator is not None and declarator.type in (
            "pointer_declarator",
            "array_declarator",
        )
        if declarator is not None and declarator.type == "pointer_declarator":
            type_text = f"{type_text} *"
        elif declarator is not None and declarator.type == "array_declarator":
            type_text = f"{type_text} []"

        params.append({
            "name": _param_name(declarator),
            "type": type_text,
            "is_pointer": is_pointer,
        })
    return params


def _param_name(declarator: Node | None) -> str | None:
    if declarator is None:
        return None
    for node in _walk(declarator):
        if node.type == "identifier":
            return _text(node)
    return None


def _is_recursive(body: Node | None, name: str) -> bool:
    if body is None:
        return False
    for node in _walk(body):
        if node.type == "call_expression":
            callee = node.child_by_field_name("function")
            if callee is not None and callee.type == "identifier" and _text(callee) == name:
                return True
    return False


def _returns_value(body: Node | None) -> bool:
    if body is None:
        return False
    for node in _walk(body):
        if node.type == "return_statement" and node.named_child_count > 0:
            return True
    return False


def _risky_loop(loop: Node) -> dict | None:
    """Off-by-one: laço com limite '<=' que indexa vetor pela variável de controle
    (só '<=' inclusivo, para evitar falso-positivo em laços reversos)."""
    condition = loop.child_by_field_name("condition")
    if condition is None:
        return None

    var = _inclusive_upper_var(condition)
    if var is None:
        return None

    if _indexes_array_with(loop, var):
        return {"var": var, "op": "<="}
    return None


def _inclusive_upper_var(condition: Node) -> str | None:
    for node in _walk(condition):
        if node.type != "binary_expression":
            continue
        op = node.child_by_field_name("operator")
        if op is None or _text(op) != "<=":
            continue
        left = node.child_by_field_name("left")
        right = node.child_by_field_name("right")
        # variável de controle é o operando identificador (geralmente à esquerda em i<=n)
        if left is not None and left.type == "identifier":
            return _text(left)
        if right is not None and right.type == "identifier":
            return _text(right)
    return None


def _indexes_array_with(loop: Node, var: str) -> bool:
    for node in _walk(loop):
        if node.type != "subscript_expression":
            continue
        index = node.child_by_field_name("index")
        if index is None:
            continue
        for inner in _walk(index):
            if inner.type == "identifier" and _text(inner) == var:
                return True
    return False
