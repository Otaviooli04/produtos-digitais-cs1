import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Check, ChevronRight, FileCode, User, X } from 'lucide-react'
import { getQuestionSubmissions } from '../api/exam'
import Spinner from '../components/Spinner'
import CodeBlock from '../components/CodeBlock'
import { compileErrorLines } from '../utils/highlightLines'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import Tag from '../components/ui/Tag'

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

  const statusVariante = (sub) => {
    if (sub.all_tests_passed) return 'sucesso'
    if (sub.compile_error) return 'erro'
    return 'aviso'
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
      <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto mb-6 lg:hidden">
        <Link to={`/exam/${id}`} className="hover:text-noite">Atividade #{id}</Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <span>Questão {num}</span>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <span>Respostas</span>
      </div>

      <div className="flex items-center gap-3 mb-6">
        <h1 className="titulo-pagina">Respostas</h1>
        <Tag variante="neutro">{data.submissions.length}</Tag>
      </div>

      {data.submissions.length === 0 ? (
        <Card className="border-dashed border-noite/30! items-center text-center py-16!">
          <FileCode className="w-10 h-10 text-violeta" aria-hidden="true" />
          <p className="text-sm text-cinza-texto">Nenhuma submissão ainda.</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {data.submissions.map(sub => (
            <div key={sub.id} className="bg-white rounded-card border-2 border-noite overflow-hidden">
              <div className="flex flex-wrap items-center justify-between gap-4 p-5">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 rounded-botao bg-lavanda flex items-center justify-center shrink-0">
                    <User className="w-4 h-4 text-violeta" aria-hidden="true" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-bold text-noite">{sub.matricula || '—'}</p>
                    <p className="text-xs text-cinza-texto">{formatDateTime(sub.submitted_at)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <Tag variante={statusVariante(sub)}>{statusLabel(sub)}</Tag>
                  <Botao variante="secundario" onClick={() => toggle(sub.id)}>
                    {expanded[sub.id] ? 'Ocultar' : 'Ver código'}
                  </Botao>
                </div>
              </div>

              {expanded[sub.id] && (
                <div className="border-t-2 border-noite/10">
                  <div className="px-4 pt-2 pb-4">
                    <CodeBlock dark code={sub.code} highlight={compileErrorLines(sub.compile_error, sub.code)} />
                  </div>

                  {sub.compile_error && (
                    <div className="px-5 py-3 border-t-2 border-noite/10">
                      <p className="text-xs font-bold text-cinza-texto mb-1.5">Erro de compilação</p>
                      <pre className="text-xs font-mono bg-erro-fundo rounded-botao p-3 text-erro overflow-x-auto whitespace-pre-wrap">{sub.compile_error}</pre>
                    </div>
                  )}

                  {sub.test_results?.length > 0 && (
                    <div className="px-5 py-3 border-t-2 border-noite/10">
                      <p className="text-xs font-bold text-cinza-texto mb-2">Testes</p>
                      <div className="space-y-2">
                        {sub.test_results.map((tr, i) => (
                          <div key={i} className={`rounded-botao border-2 px-3 py-2 ${tr.passed ? 'bg-sucesso-fundo border-sucesso' : 'bg-erro-fundo border-erro'}`}>
                            <div className="flex items-center gap-1.5 mb-1">
                              <span className={`inline-flex items-center gap-1 text-xs font-bold ${tr.passed ? 'text-sucesso' : 'text-erro'}`}>
                                {tr.passed ? <Check className="w-3.5 h-3.5" aria-hidden="true" /> : <X className="w-3.5 h-3.5" aria-hidden="true" />} Teste {i + 1}
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
