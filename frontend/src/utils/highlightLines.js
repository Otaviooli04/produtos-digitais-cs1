// Linhas (1-based) marcadas como 'error' pelo gcc, para destacar no front (espelha error_locator.py).
const GCC_LINE = /^[^\s:]+:(\d+):(?:\d+:)?\s*(error|warning|note)\b/gm

export function compileErrorLines(compileError, code) {
  if (!compileError) return []
  const max = (code || '').split('\n').length
  const out = new Set()
  let m
  while ((m = GCC_LINE.exec(compileError)) !== null) {
    if (m[2] !== 'error') continue // avisos/notas não marcam a parte culpada
    const n = parseInt(m[1], 10)
    if (n >= 1 && n <= max) out.add(n)
  }
  return [...out].sort((a, b) => a - b)
}
