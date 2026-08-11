// Barras horizontais em CSS para rankings simples.
// items: [{ label, value, display?, title?, color? }]; max: teto da largura (default: maior value).
export default function BarList({ items, max, color = '#7c3aed' }) {
  const top = max ?? Math.max(1, ...items.map(i => i.value))
  return (
    <div className="space-y-3">
      {items.map((it, i) => (
        <div key={i} className="flex items-center gap-3 text-xs">
          <span className="w-28 shrink-0 truncate text-gray-600" title={it.title ?? it.label}>
            {it.label}
          </span>
          <div className="flex-1 bg-gray-100 rounded-full h-2.5 overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${Math.min(100, (it.value / top) * 100)}%`, backgroundColor: it.color ?? color }}
            />
          </div>
          <span className="w-12 shrink-0 text-right font-medium text-gray-700">
            {it.display ?? it.value}
          </span>
        </div>
      ))}
    </div>
  )
}
