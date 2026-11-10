import { Search } from 'lucide-react'

// Controles de lista reutilizáveis: busca por texto + ordenação.
// Usado nas listas de turmas e de provas.
export default function ListControls({ search, onSearch, sort, onSort, sortOptions, placeholder = 'Buscar…' }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-4">
      <div className="relative flex-1">
        <Search
          className="w-4 h-4 text-violeta absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
          aria-hidden="true"
        />
        <input
          type="text"
          value={search}
          onChange={e => onSearch(e.target.value)}
          placeholder={placeholder}
          className="campo pl-9!"
        />
      </div>
      <select
        value={sort}
        onChange={e => onSort(e.target.value)}
        className="campo sm:w-auto!"
      >
        {sortOptions.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  )
}
