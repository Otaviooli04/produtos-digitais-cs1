import { Link } from 'react-router-dom'

// Chips das matrículas onde um erro aparece, cada uma linkando para o detalhe do aluno.
export default function WhoList({ examId, matriculas }) {
  if (!matriculas?.length) {
    return <p className="text-xs text-cinza-texto italic">Sem matrícula identificada.</p>
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {matriculas.map(m => (
        <Link
          key={m}
          to={`/exam/${examId}/students/${encodeURIComponent(m)}`}
          className="text-xs font-mono bg-lavanda hover:bg-lavanda text-cinza-texto hover:text-violeta px-2 py-0.5 rounded-md transition-colors"
        >
          {m}
        </Link>
      ))}
    </div>
  )
}
