// Exibe o resultado da verificação de funções (function_check) de uma submissão.
// Só faz sentido renderizar quando a questão exige funções e há alguma divergência.
export default function FunctionCheckCard({ check }) {
  if (!check) return null

  const rows = [
    { label: 'Funções ausentes', items: check.missing_functions, tone: 'text-red-600' },
    { label: 'Assinatura incorreta', items: check.signature_mismatches, tone: 'text-orange-600' },
    { label: 'Deveriam ser recursivas', items: check.missing_recursion, tone: 'text-orange-600' },
    { label: 'Deveriam receber ponteiro', items: check.missing_pointer_param, tone: 'text-orange-600' },
  ].filter((r) => r.items && r.items.length > 0)

  if (rows.length === 0) return null

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="text-sm font-medium text-gray-700 mb-2">Verificação de funções</h3>
      <ul className="text-xs text-gray-700 space-y-1.5">
        {rows.map((r) => (
          <li key={r.label}>
            <span className="text-gray-500">{r.label}:</span>{' '}
            <span className={r.tone}>{r.items.join('; ')}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
