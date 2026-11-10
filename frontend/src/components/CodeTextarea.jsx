import { useLayoutEffect, useRef, useState } from 'react'

const RECUO = '    '
const LARGURA_DA_NUMERACAO = '2.75rem'

/**
 * Textarea para código C. Tab recua em vez de sair do campo (Esc libera o
 * próximo Tab para sair), Shift+Tab desfaz o recuo, e Enter mantém o recuo da
 * linha, com um nível a mais depois de `{`. As linhas são numeradas porque o
 * diagnóstico e a explicação citam a linha do erro.
 *
 * Mesmas props de um textarea, e `onChange` recebe o evento nativo.
 */
export default function CodeTextarea({ value, onChange, onKeyDown, className = '', style, ...props }) {
  const ref = useRef(null)
  const numeracao = useRef(null)
  const sairNoProximoTab = useRef(false)
  const [medidas, setMedidas] = useState(null)

  // A numeração copia fonte, altura de linha e recuo de cima (padding mais
  // borda) do próprio campo, que muda de tamanho entre as telas. Mede de novo
  // quando o campo muda, porque girar o celular cruza o ponto em que a fonte troca.
  useLayoutEffect(() => {
    const campo = ref.current
    if (!campo) return
    const medir = () => {
      const css = getComputedStyle(campo)
      setMedidas({
        fontSize: css.fontSize,
        lineHeight: css.lineHeight,
        paddingTop: `${parseFloat(css.paddingTop) + parseFloat(css.borderTopWidth)}px`,
      })
    }
    medir()
    const observador = new ResizeObserver(medir)
    observador.observe(campo)
    return () => observador.disconnect()
  }, [])

  const sincronizar = () => {
    if (numeracao.current && ref.current) numeracao.current.scrollTop = ref.current.scrollTop
  }

  // Troca o trecho [ini, fim) pelo novo texto como se o aluno tivesse digitado:
  // o navegador guarda no histórico do Ctrl+Z e dispara o onChange sozinho.
  // Se o navegador recusar, cai no onChange direto, sem o desfazer.
  const substituir = (el, ini, fim, texto, cursorIni, cursorFim) => {
    el.setSelectionRange(ini, fim)
    const nativo = texto === el.value.slice(ini, fim) || document.execCommand('insertText', false, texto)
    if (!nativo) {
      el.value = el.value.slice(0, ini) + texto + el.value.slice(fim)
      onChange?.({ target: el, currentTarget: el })
    }
    el.setSelectionRange(cursorIni, cursorFim)
  }

  const handleKeyDown = (e) => {
    onKeyDown?.(e)
    if (e.defaultPrevented || props.disabled || props.readOnly || e.nativeEvent.isComposing) return
    const el = e.currentTarget

    if (e.key === 'Escape') {
      sairNoProximoTab.current = true
      return
    }
    if (e.key === 'Tab' && sairNoProximoTab.current) {
      sairNoProximoTab.current = false
      return
    }
    sairNoProximoTab.current = false

    const texto = el.value
    const { selectionStart: ini, selectionEnd: fim } = el

    if (e.key === 'Tab') {
      e.preventDefault()
      if (!e.shiftKey && ini === fim) {
        substituir(el, ini, fim, RECUO, ini + RECUO.length, ini + RECUO.length)
        return
      }

      // Com seleção (ou Shift+Tab), recua ou desfaz o recuo das linhas tocadas.
      // A seleção que termina no começo de uma linha não leva essa linha junto.
      const fimEfetivo = fim > ini && texto[fim - 1] === '\n' ? fim - 1 : fim
      const inicioDaLinha = texto.lastIndexOf('\n', ini - 1) + 1
      const linhas = texto.slice(inicioDaLinha, fimEfetivo).split('\n')
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
      const novoIni = Math.max(inicioDaLinha, ini + primeira)
      const novoFim = ini === fim ? novoIni : fim + total
      substituir(el, inicioDaLinha, fimEfetivo, novas.join('\n'), novoIni, novoFim)
      return
    }

    if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
      e.preventDefault()
      const inicioDaLinha = texto.lastIndexOf('\n', ini - 1) + 1
      const recuoAtual = texto.slice(inicioDaLinha, ini).match(/^[ \t]*/)[0]
      const extra = texto.slice(0, ini).trimEnd().endsWith('{') ? RECUO : ''
      const inserir = '\n' + recuoAtual + extra
      substituir(el, ini, fim, inserir, ini + inserir.length, ini + inserir.length)
    }
  }

  const linhas = Math.max(1, (value ?? '').split('\n').length)

  return (
    <div className="relative">
      <div
        ref={numeracao}
        aria-hidden="true"
        className="pointer-events-none absolute inset-y-0 left-0 select-none overflow-hidden text-right font-mono tabular-nums text-white/60 pr-2"
        style={{ width: LARGURA_DA_NUMERACAO, ...(medidas ?? {}) }}
      >
        {Array.from({ length: linhas }, (_, i) => <div key={i}>{i + 1}</div>)}
      </div>
      <textarea
        ref={ref}
        value={value}
        onChange={onChange}
        onKeyDown={handleKeyDown}
        onScroll={sincronizar}
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        wrap="off"
        className={className}
        style={{ ...style, paddingLeft: `calc(${LARGURA_DA_NUMERACAO} + 0.5rem)` }}
        {...props}
      />
    </div>
  )
}
