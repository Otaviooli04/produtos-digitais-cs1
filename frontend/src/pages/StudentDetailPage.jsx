import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getStudentDetail } from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import CodeBlock from '../components/CodeBlock'
import { compileErrorLines } from '../utils/highlightLines'

export default function StudentDetailPage() {
  const { id, matricula } = useParams()
  const decoded = decodeURIComponent(matricula)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    getStudentDetail(id, decoded)
      .then(({ data: d }) => setData(d))
      .catch(() => setError('Erro ao carregar dados do aluno.'))
      .finally(() => setLoading(false))
  }, [id, decoded])

  const toggle = (qnum) => setExpanded(prev => ({ ...prev, [qnum]: !prev[qnum] }))

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  if (error) return <p className="text-red-600 text-sm">{error}</p>

  const diagColor = (sub) => {
    if (sub.all_tests_passed) return 'green'
    if (sub.compile_error) return 'red'
    if (sub.submission_id) return 'yellow'
    return 'gray'
  }

  const diagLabel = (sub) => {
    if (!sub.submission_id) return 'Não respondeu'
    if (sub.all_tests_passed) return 'Correto'
    if (sub.compile_error) return 'Erro de compilação'
    return sub.error_category || 'Incorreto'
  }

  const formatDate = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <Link to={`/exam/${id}/students`} className="hover:text-gray-600">Alunos</Link>
        <span>›</span>
        <span className="text-gray-600">{decoded}</span>
      </div>

      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center shrink-0">
            <span className="text-base font-bold text-purple-600">{decoded[0]?.toUpperCase()}</span>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-gray-900">{decoded}</h1>
            <p className="text-xs text-gray-400">
              {data.answered_count} de {data.total_questions} questões respondidas
            </p>
          </div>
        </div>

        <div className="flex gap-3">
          <div className="flex-1 rounded-lg bg-gray-50 border border-gray-200 p-3 text-center">
            <p className="text-xl font-bold text-gray-900">{data.passed_count}</p>
            <p className="text-xs text-gray-400">Corretas</p>
          </div>
          <div className="flex-1 rounded-lg bg-gray-50 border border-gray-200 p-3 text-center">
            <p className="text-xl font-bold text-gray-900">{data.answered_count - data.passed_count}</p>
            <p className="text-xs text-gray-400">Incorretas</p>
          </div>
          <div className="flex-1 rounded-lg bg-gray-50 border border-gray-200 p-3 text-center">
            <p className="text-xl font-bold text-gray-900">{data.total_questions - data.answered_count}</p>
            <p className="text-xs text-gray-400">Não respondidas</p>
          </div>
          <div className="flex-1 rounded-lg bg-purple-50 border border-purple-200 p-3 text-center">
            <p className="text-xl font-bold text-purple-700">
              {data.answered_count > 0 ? Math.round(data.passed_count / data.answered_count * 100) : 0}%
            </p>
            <p className="text-xs text-purple-500">Aproveitamento</p>
          </div>
        </div>
      </div>

      {/* Questões */}
      <div className="space-y-3">
        {data.submissions.map(sub => (
          <div key={sub.question_number} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="flex items-start gap-4 p-5">
              <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded-md shrink-0 mt-0.5">
                Q{sub.question_number}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-700 line-clamp-2">{sub.statement}</p>
                {sub.submitted_at && (
                  <p className="text-xs text-gray-400 mt-1">{formatDate(sub.submitted_at)}</p>
                )}
                {sub.cluster_dominant_error && (
                  <Link
                    to={`/exam/${id}/questions/${sub.question_number}?tab=cluster`}
                    className="inline-flex items-center gap-1 mt-1.5 text-xs px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors"
                    title="Ver os grupos de dificuldade desta questão"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0" />
                    Grupo: {sub.cluster_dominant_error}{sub.cluster_size ? ` (${sub.cluster_size})` : ''}
                  </Link>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge color={diagColor(sub)}>{diagLabel(sub)}</Badge>
                {sub.submission_id && (
                  <button
                    onClick={() => toggle(sub.question_number)}
                    className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                  >
                    {expanded[sub.question_number] ? 'Ocultar' : 'Ver código'}
                  </button>
                )}
              </div>
            </div>

            {!sub.submission_id && (
              <div className="px-5 pb-4">
                <p className="text-xs text-gray-400 italic">Questão não respondida por este aluno.</p>
              </div>
            )}

            {sub.submission_id && expanded[sub.question_number] && (
              <div className="border-t border-gray-100">
                <div className="px-4 pt-2 pb-4">
                  <CodeBlock dark code={sub.code} highlight={compileErrorLines(sub.compile_error, sub.code)} />
                </div>

                {sub.compile_error && (
                  <div className="px-5 py-3 border-t border-gray-100">
                    <p className="text-xs font-medium text-gray-500 mb-1.5">Erro de compilação</p>
                    <pre className="text-xs font-mono bg-red-50 rounded-lg p-3 text-red-700 overflow-x-auto whitespace-pre-wrap">{sub.compile_error}</pre>
                  </div>
                )}

                {sub.pedagogical_diagnosis && (
                  <div className="px-5 py-3 border-t border-gray-100">
                    <p className="text-xs font-medium text-gray-500 mb-1">Diagnóstico</p>
                    <p className="text-sm text-gray-700">{sub.pedagogical_diagnosis}</p>
                    {sub.actionable_feedback && (
                      <div className="mt-2 rounded-lg bg-blue-50 border border-blue-100 px-3 py-2">
                        <p className="text-xs text-blue-700">{sub.actionable_feedback}</p>
                      </div>
                    )}
                  </div>
                )}

                {sub.test_results.length > 0 && (
                  <div className="px-5 py-3 border-t border-gray-100">
                    <p className="text-xs font-medium text-gray-500 mb-2">Testes</p>
                    <div className="space-y-1.5">
                      {sub.test_results.map((tr, i) => (
                        <div key={i} className={`rounded-lg border px-3 py-2 ${tr.passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                          <div className="flex items-center gap-1.5 mb-1">
                            <span className={`text-xs font-semibold ${tr.passed ? 'text-green-700' : 'text-red-700'}`}>
                              {tr.passed ? '✓' : '✗'} Teste {i + 1}
                            </span>
                          </div>
                          <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                            <div><span className="text-gray-400">entrada:</span> <span className="text-gray-700">{tr.input || '(vazia)'}</span></div>
                            <div><span className="text-gray-400">esperado:</span> <span className="text-gray-700">{tr.expected_output}</span></div>
                            <div><span className="text-gray-400">obtido:</span> <span className={tr.passed ? 'text-green-700' : 'text-red-700'}>{tr.actual_output}</span></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
