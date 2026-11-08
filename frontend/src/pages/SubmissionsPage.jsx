import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getQuestionSubmissions } from '../api/exam'
import Spinner from '../components/Spinner'
import CodeBlock from '../components/CodeBlock'
import { compileErrorLines } from '../utils/highlightLines'

export default function SubmissionsPage() {
  const { id, num } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState({})

  useEffect(() => {
    getQuestionSubmissions(id, num)
      .then(({ data: d }) => setData(d))
      .catch(() => setError('Erro ao carregar submissões.'))
      .finally(() => setLoading(false))
  }, [id, num])

  const toggle = (subId) => setExpanded(prev => ({ ...prev, [subId]: !prev[subId] }))

  const formatDateTime = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  const statusColor = (sub) => {
    if (sub.all_tests_passed) return 'bg-sucesso-fundo text-sucesso border-sucesso/30'
    if (sub.compile_error) return 'bg-erro-fundo text-erro border-erro/30'
    return 'bg-aviso-fundo text-aviso border-aviso/30'
  }

  const statusLabel = (sub) => {
    if (sub.all_tests_passed) return 'Correto'
    if (sub.compile_error) return 'Erro de compilação'
    return sub.error_category || 'Incorreto'
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>
  if (error) return <p className="text-erro text-sm">{error}</p>

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-cinza-texto mb-6">
        <Link to={`/exam/${id}`} className="hover:text-cinza-texto">Atividade #{id}</Link>
        <span>›</span>
        <span>Questão {num}</span>
        <span>›</span>
        <span className="text-cinza-texto">Respostas</span>
      </div>

      <div className="flex items-center gap-3 mb-6">
        <h1 className="text-xl font-semibold text-noite">Respostas</h1>
        <span className="text-xs font-medium text-cinza-texto bg-lavanda px-2 py-0.5 rounded-full">
          {data.submissions.length}
        </span>
      </div>

      {data.submissions.length === 0 ? (
        <div className="text-center py-16 text-cinza-texto">
          <svg className="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
          </svg>
          <p className="text-sm">Nenhuma submissão ainda.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.submissions.map(sub => (
            <div key={sub.id} className="bg-white rounded-xl border border-noite/20 overflow-hidden">
              <div className="flex items-center justify-between gap-4 p-5">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-8 h-8 rounded-full bg-lavanda flex items-center justify-center shrink-0">
                    <svg className="w-4 h-4 text-violeta" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-noite">{sub.matricula || '—'}</p>
                    <p className="text-xs text-cinza-texto">{formatDateTime(sub.submitted_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-md border ${statusColor(sub)}`}>
                    {statusLabel(sub)}
                  </span>
                  <button
                    onClick={() => toggle(sub.id)}
                    className="text-xs px-2.5 py-1.5 rounded-md border border-noite/20 text-cinza-texto hover:bg-lavanda transition-colors"
                  >
                    {expanded[sub.id] ? 'Ocultar' : 'Ver código'}
                  </button>
                </div>
              </div>

              {expanded[sub.id] && (
                <div className="border-t border-noite/10">
                  <div className="px-4 pt-2 pb-4">
                    <CodeBlock dark code={sub.code} highlight={compileErrorLines(sub.compile_error, sub.code)} />
                  </div>

                  {sub.compile_error && (
                    <div className="px-5 py-3 border-t border-noite/10">
                      <p className="text-xs font-medium text-cinza-texto mb-1.5">Erro de compilação</p>
                      <pre className="text-xs font-mono bg-erro-fundo rounded-lg p-3 text-erro overflow-x-auto whitespace-pre-wrap">{sub.compile_error}</pre>
                    </div>
                  )}

                  {sub.test_results?.length > 0 && (
                    <div className="px-5 py-3 border-t border-noite/10">
                      <p className="text-xs font-medium text-cinza-texto mb-2">Testes</p>
                      <div className="space-y-2">
                        {sub.test_results.map((tr, i) => (
                          <div key={i} className={`rounded-lg border px-3 py-2 ${tr.passed ? 'bg-sucesso-fundo border-sucesso/30' : 'bg-erro-fundo border-erro/30'}`}>
                            <div className="flex items-center gap-1.5 mb-1">
                              <span className={`text-xs font-semibold ${tr.passed ? 'text-sucesso' : 'text-erro'}`}>
                                {tr.passed ? '✓' : '✗'} Teste {i + 1}
                              </span>
                            </div>
                            <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                              <div><span className="text-cinza-texto">entrada:</span> <span className="text-cinza-texto">{tr.input || '(vazia)'}</span></div>
                              <div><span className="text-cinza-texto">esperado:</span> <span className="text-cinza-texto">{tr.expected_output}</span></div>
                              <div><span className="text-cinza-texto">obtido:</span> <span className={tr.passed ? 'text-sucesso' : 'text-erro'}>{tr.actual_output}</span></div>
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
      )}
    </div>
  )
}
