// Código numerado; linhas em `highlight` (1-based) recebem destaque. `dark`: tema escuro.
export default function CodeBlock({ code, highlight = [], dark = false }) {
  const hot = new Set(highlight)
  const lines = (code || '').split('\n')
  const t = dark
    ? { box: 'bg-gray-900', gutter: 'text-gray-600', text: 'text-green-400',
        hotRow: 'bg-red-500/15', hotGutter: 'text-red-400', hotText: 'text-red-300' }
    : { box: 'bg-gray-50', gutter: 'text-gray-300', text: 'text-gray-600',
        hotRow: 'bg-red-50', hotGutter: 'text-red-400', hotText: 'text-red-700' }
  return (
    <div className={`mt-2 text-xs font-mono ${t.box} rounded-lg overflow-x-auto max-h-60`}>
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
