import { COR_PADRAO } from '../utils/coresGraficos'

// Barras horizontais em CSS para rankings simples.
// items: [{ label, value, display?, title?, color? }]; max: teto da largura (default: maior value).
export default function BarList({ items, max, color = COR_PADRAO }) {
  const top = max ?? Math.max(1, ...items.map(i => i.value))
  return (
    <div className="space-y-3">
      {items.map((it, i) => (
        <div key={i} className="flex items-center gap-3 text-sm">
          <span className="w-28 shrink-0 truncate text-cinza-texto" title={it.title ?? it.label}>
            {it.label}
          </span>
          <div className="flex-1 bg-lavanda rounded-[5px] h-2.5 overflow-hidden">
            <div
              className="h-full rounded-[5px]"
              style={{ width: `${Math.min(100, (it.value / top) * 100)}%`, backgroundColor: it.color ?? color }}
            />
          </div>
          <span className="w-12 shrink-0 text-right font-bold text-noite">
            {it.display ?? it.value}
          </span>
        </div>
      ))}
    </div>
  )
}
