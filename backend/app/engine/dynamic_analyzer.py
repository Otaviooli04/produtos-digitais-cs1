import subprocess
import tempfile
import os


def _normalize_ws(text: str) -> str:
    """Colapsa espaços horizontais e apara linhas em branco nas bordas, preservando quebras de linha."""
    lines = [" ".join(line.split()) for line in text.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


_RUN_BACKUP_TIMEOUT_S = 15  # backup do subprocess; o limite real é o "timeout 5" no container


def _run_once(run_cmd: list[str], stdin: str):
    """Executa o binário no container. Retorna ("ok", saida), ("timeout", None) em
    laço infinito (returncode 124) ou ("hiccup", None) quando o Docker está lento."""
    try:
        r = subprocess.run(run_cmd, input=stdin, capture_output=True,
                           text=True, timeout=_RUN_BACKUP_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return "hiccup", None
    if r.returncode == 124:
        return "timeout", None
    return "ok", r.stdout.strip()


def compile_and_run(source_code: str, test_cases: list[dict]) -> dict:
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "student_code.c")
        with open(source_path, "w", encoding="utf-8") as f:
            f.write(source_code)

        compile_cmd = [
            "docker", "run", "--rm", "--network", "none",
            "-v", f"{temp_dir}:/src", "-w", "/src",
            "gcc:latest",
            # -lm linka a libm; -ftrivial-auto-var-init=zero zera locais não inicializadas (alinha ao CodeRunner)
            "gcc", "-Wall", "-ftrivial-auto-var-init=zero",
            "student_code.c", "-o", "exe.out", "-lm",
        ]
        try:
            compile_result = subprocess.run(
                compile_cmd, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            try:  # timeout aqui costuma ser lentidão do Docker, não o gcc: nova tentativa
                compile_result = subprocess.run(
                    compile_cmd, capture_output=True, text=True, timeout=60)
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "compile_error": "A compilação não terminou no tempo limite "
                                     "(Docker indisponível no momento). Reavalie a submissão.",
                    "warnings": "",
                    "test_results": [],
                    "all_tests_passed": None,
                }

        if compile_result.returncode != 0:
            return {
                "success": False,
                "compile_error": compile_result.stderr or compile_result.stdout,
                "warnings": "",
                "test_results": [],
                "all_tests_passed": None,
            }

        warnings = compile_result.stderr.strip()

        if not test_cases:
            return {
                "success": True,
                "compile_error": "",
                "warnings": warnings,
                "test_results": [],
                "all_tests_passed": None,
            }

        run_cmd = [
            "docker", "run", "--rm", "--network", "none", "-i",
            "-v", f"{temp_dir}:/src", "-w", "/src",
            "gcc:latest", "timeout", "5", "./exe.out",
        ]
        test_results = []
        for tc in test_cases:
            status, out = _run_once(run_cmd, tc["input"])
            if status == "hiccup":  # lentidão do Docker: 1 nova tentativa
                status, out = _run_once(run_cmd, tc["input"])
            actual = out if status == "ok" else "TIMEOUT"
            expected = tc["expected_output"].strip()
            test_results.append({
                "input": tc["input"],
                "expected_output": expected,
                "actual_output": actual,
                "passed": _normalize_ws(actual) == _normalize_ws(expected),
            })

        return {
            "success": True,
            "compile_error": "",
            "warnings": warnings,
            "test_results": test_results,
            "all_tests_passed": all(r["passed"] for r in test_results),
        }
