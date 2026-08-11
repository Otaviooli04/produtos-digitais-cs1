import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getExamStudents } from '../api/exam'
import Spinner from '../components/Spinner'

function StatusCell({ status }) {
  if (status.submission_id === null) {
    return (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-gray-100 text-gray-400 text-xs">
        —
      </span>
    )
  }
  if (status.passed) {
    return (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-green-100 text-green-700 text-xs font-semibold">
        ✓
      </span>
    )
  }
  if (status.compile_error) {
    return (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-red-100 text-red-700 text-xs font-semibold" title={status.error_category}>
        ✗
      </span>
    )
  }
  return (
    <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-yellow-100 text-yellow-700 text-xs font-semibold" title={status.error_category}>
      ~
    </span>
  )
}

export default function StudentsPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getExamStudents(id)
      .then(({ data: d }) => setData(d))
      .catch(() => setError('Erro ao carregar alunos.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  if (error) return <p className="text-red-600 text-sm">{error}</p>

  const totalStudents = data.students.length
  const avgPass = totalStudents > 0
    ? Math.round(data.students.reduce((acc, s) => acc + (s.answered_count > 0 ? s.passed_count / s.answered_count : 0), 0) / totalStudents * 100)
    : 0

  const atRisk = data.students
    .filter(s => s.answered_count > 0 && s.passed_count / s.answered_count < 0.4)
    .sort((a, b) => (a.passed_count / a.answered_count) - (b.passed_count / b.answered_count))

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <span className="text-gray-600">Alunos</span>
      </div>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Alunos</h1>
        <div className="flex gap-4 text-sm text-gray-500">
          <span><span className="font-semibold text-gray-900">{totalStudents}</span> alunos</span>
          <span><span className="font-semibold text-gray-900">{avgPass}%</span> acerto médio</span>
        </div>
      </div>

      {atRisk.length > 0 && (
        <div className="mb-6 rounded-xl border border-red-100 bg-red-50/60 p-4">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
            </svg>
            <h2 className="text-sm font-semibold text-red-700">Alunos em risco ({atRisk.length})</h2>
            <span className="text-xs text-red-500">menos de 40% de acerto</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {atRisk.map(s => {
              const pct = Math.round(s.passed_count / s.answered_count * 100)
              return (
                <button
                  key={s.matricula}
                  onClick={() => navigate(`/exam/${id}/students/${encodeURIComponent(s.matricula)}`)}
                  className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs hover:border-red-300 hover:shadow-sm transition-all"
                >
                  <span className="font-medium text-gray-900">{s.matricula}</span>
                  <span className="text-red-600 font-semibold">{s.passed_count}/{s.answered_count} ({pct}%)</span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {totalStudents === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <svg className="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
          <p className="text-sm">Nenhuma submissão com matrícula ainda.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 min-w-[180px]">Matrícula</th>
                {data.question_numbers.map(num => (
                  <th key={num} className="px-3 py-3 text-xs font-medium text-gray-500 text-center">
                    Q{num}
                  </th>
                ))}
                <th className="px-5 py-3 text-xs font-medium text-gray-500 text-right">Acertos</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data.students.map(student => {
                const pct = student.answered_count > 0
                  ? Math.round(student.passed_count / student.answered_count * 100)
                  : null
                return (
                  <tr
                    key={student.matricula}
                    onClick={() => navigate(`/exam/${id}/students/${encodeURIComponent(student.matricula)}`)}
                    className="hover:bg-purple-50 cursor-pointer transition-colors"
                  >
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-purple-100 flex items-center justify-center shrink-0">
                          <span className="text-xs font-semibold text-purple-600">
                            {student.matricula?.[0]}
                          </span>
                        </div>
                        <span className="font-medium text-gray-900 truncate max-w-[140px]">{student.matricula}</span>
                      </div>
                    </td>
                    {student.questions.map(qs => (
                      <td key={qs.question_number} className="px-3 py-3 text-center">
                        <StatusCell status={qs} />
                      </td>
                    ))}
                    <td className="px-5 py-3 text-right">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                        pct === null ? 'text-gray-400 bg-gray-100'
                        : pct >= 70 ? 'text-green-700 bg-green-100'
                        : pct >= 40 ? 'text-yellow-700 bg-yellow-100'
                        : 'text-red-700 bg-red-100'
                      }`}>
                        {student.passed_count}/{student.answered_count}
                        {pct !== null && ` (${pct}%)`}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 flex items-center gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-5 rounded-full bg-green-100 text-green-700 flex items-center justify-center font-semibold">✓</span> Correto
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-5 rounded-full bg-yellow-100 text-yellow-700 flex items-center justify-center font-semibold">~</span> Incorreto
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-5 rounded-full bg-red-100 text-red-700 flex items-center justify-center font-semibold">✗</span> Erro de compilação
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-5 rounded-full bg-gray-100 text-gray-400 flex items-center justify-center">—</span> Não respondeu
        </span>
      </div>
    </div>
  )
}
