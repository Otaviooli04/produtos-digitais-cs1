import { Link } from 'react-router-dom'

// Chips das matrículas onde um erro aparece, cada uma linkando para o detalhe do aluno.
export default function WhoList({ examId, matriculas }) {
  if (!matriculas?.length) {
    return <p className="text-xs text-gray-400 italic">Sem matrícula identificada.</p>
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {matriculas.map(m => (
        <Link
          key={m}
          to={`/exam/${examId}/students/${encodeURIComponent(m)}`}
          className="text-xs font-mono bg-gray-100 hover:bg-purple-100 text-gray-600 hover:text-purple-700 px-2 py-0.5 rounded-md transition-colors"
        >
          {m}
        </Link>
      ))}
    </div>
  )
}
