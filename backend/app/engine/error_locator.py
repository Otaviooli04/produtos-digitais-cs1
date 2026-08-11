"""Extrai do output do gcc as linhas com erro de compilação (1:1 com o código submetido)."""
import re

# "arquivo.c:LINHA[:COL]: error|warning|note"; só 'error' marca a linha culpada
_GCC_LINE = re.compile(
    r"^[^\s:]+:(\d+):(?:\d+:)?\s*(error|warning|note)\b", re.MULTILINE
)


def parse_compile_error_lines(compile_error: str, max_line: int | None = None) -> list[int]:
    """Linhas (1-based, ordenadas, únicas) marcadas como erro; max_line descarta fora do intervalo."""
    if not compile_error:
        return []
    lines: set[int] = set()
    for m in _GCC_LINE.finditer(compile_error):
        if m.group(2) != "error":
            continue
        n = int(m.group(1))
        if n < 1 or (max_line is not None and n > max_line):
            continue
        lines.add(n)
    return sorted(lines)
