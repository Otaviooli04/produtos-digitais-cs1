import { useLayoutEffect, useRef } from 'react'

const RECUO = '    '

/**
 * Textarea para código C. Tab recua em vez de sair do campo, Shift+Tab desfaz o
 * recuo, e Enter mantém o recuo da linha (com um nível a mais depois de `{`).
 * Mesmas props de um textarea: `onChange` recebe `{ target: { value } }`.
 */
export default function CodeTextarea({ value, onChange, onKeyDown, ...props }) {
  const ref = useRef(null)
  const cursor = useRef(null)

  useLayoutEffect(() => {
    if (cursor.current && ref.current) {
      ref.current.setSelectionRange(cursor.current[0], cursor.current[1])
      cursor.current = null
    }
  }, [value])

  const aplicar = (novo, inicio, fim) => {
    cursor.current = [inicio, fim]
    onChange?.({ target: { value: novo } })
  }

  const handleKeyDown = (e) => {
    onKeyDown?.(e)
    if (e.defaultPrevented || props.disabled || props.readOnly) return
    const el = e.target
    const { selectionStart: ini, selectionEnd: fim } = el
    const texto = value ?? ''

    if (e.key === 'Tab') {
      e.preventDefault()
      const inicioDaLinha = texto.lastIndexOf('\n', ini - 1) + 1
      const variasLinhas = texto.slice(ini, fim).includes('\n')

      if (!e.shiftKey && !variasLinhas) {
        aplicar(texto.slice(0, ini) + RECUO + texto.slice(fim), ini + RECUO.length, ini + RECUO.length)
        return
      }

      const bloco = texto.slice(inicioDaLinha, fim)
      const linhas = bloco.split('\n')
      let primeira = 0
      let total = 0
      const novas = linhas.map((linha, i) => {
        if (!e.shiftKey) {
          total += RECUO.length
          if (i === 0) primeira = RECUO.length
          return RECUO + linha
        }
        const tirar = linha.match(/^( {1,4}|\t)/)?.[0].length ?? 0
        total -= tirar
        if (i === 0) primeira = -tirar
        return linha.slice(tirar)
      })
      const novo = texto.slice(0, inicioDaLinha) + novas.join('\n') + texto.slice(fim)
      const novoIni = Math.max(inicioDaLinha, ini + primeira)
      aplicar(novo, novoIni, fim + total)
      return
    }

    if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault()
      const inicioDaLinha = texto.lastIndexOf('\n', ini - 1) + 1
      const recuoAtual = texto.slice(inicioDaLinha, ini).match(/^[ \t]*/)[0]
      const antes = texto.slice(0, ini).trimEnd()
      const extra = antes.endsWith('{') ? RECUO : ''
      const inserir = '\n' + recuoAtual + extra
      aplicar(texto.slice(0, ini) + inserir + texto.slice(fim), ini + inserir.length, ini + inserir.length)
    }
  }

  return (
    <textarea
      ref={ref}
      value={value}
      onChange={onChange}
      onKeyDown={handleKeyDown}
      spellCheck={false}
      autoCapitalize="off"
      autoCorrect="off"
      {...props}
    />
  )
}
