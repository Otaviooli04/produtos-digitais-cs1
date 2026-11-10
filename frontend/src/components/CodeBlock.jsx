// Código numerado; linhas em `highlight` (1-based) recebem destaque. `dark`: tema escuro.
export default function CodeBlock({ code, highlight = [], dark = false }) {
  const hot = new Set(highlight)
  const lines = (code || '').split('\n')
  const t = dark
    ? { box: 'bg-noite', gutter: 'text-white/40', text: 'text-codigo-sucesso',
        hotRow: 'bg-erro/15', hotGutter: 'text-codigo-erro', hotText: 'text-codigo-erro' }
    : { box: 'bg-lavanda', gutter: 'text-cinza-texto', text: 'text-cinza-texto',
        hotRow: 'bg-erro-fundo', hotGutter: 'text-erro', hotText: 'text-erro' }
  return (
    <div className={`mt-2 text-xs font-mono ${t.box} rounded-botao overflow-x-auto max-h-60`}>
      <table className="w-full border-collapse">
        <tbody>
          {lines.map((ln, i) => {
            const n = i + 1
            const flagged = hot.has(n)
            return (
              <tr key={n} className={flagged ? t.hotRow : ''}>
                <td
                  className={`select-none text-right px-3 align-top tabular-nums ${
                    flagged ? `${t.hotGutter} font-medium` : t.gutter
                  }`}
                >
                  {n}
                </td>
                <td className={`pr-3 whitespace-pre align-top ${flagged ? t.hotText : t.text}`}>
                  {ln || ' '}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
