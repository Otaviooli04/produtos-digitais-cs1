import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Check, ChevronRight, X } from 'lucide-react'
import { getStudentDetail } from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import CodeBlock from '../components/CodeBlock'
import { compileErrorLines } from '../utils/highlightLines'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import Tag from '../components/ui/Tag'

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

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>
  if (error) return <p className="text-erro text-sm">{error}</p>

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
      <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto mb-6 lg:hidden">
        <Link to={`/exam/${id}`} className="hover:text-noite">Atividade #{id}</Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <Link to={`/exam/${id}/students`} className="hover:text-noite">Alunos</Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <span>{decoded}</span>
      </div>

      {/* Header */}
      <Card principal className="mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-botao bg-lavanda flex items-center justify-center shrink-0">
            <span className="text-base font-extrabold text-violeta">{decoded[0]?.toUpperCase()}</span>
          </div>
          <div>
            <h1 className="titulo-card">{decoded}</h1>
            <p className="text-xs text-cinza-texto">
              {data.answered_count} de {data.total_questions} questões respondidas
            </p>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-24 rounded-botao bg-lavanda p-3 text-center">
            <p className="text-xl font-extrabold font-titulo text-noite">{data.passed_count}</p>
            <p className="text-xs text-cinza-texto">Corretas</p>
          </div>
          <div className="flex-1 min-w-24 rounded-botao bg-lavanda p-3 text-center">
            <p className="text-xl font-extrabold font-titulo text-noite">{data.answered_count - data.passed_count}</p>
            <p className="text-xs text-cinza-texto">Incorretas</p>
          </div>
          <div className="flex-1 min-w-24 rounded-botao bg-lavanda p-3 text-center">
            <p className="text-xl font-extrabold font-titulo text-noite">{data.total_questions - data.answered_count}</p>
            <p className="text-xs text-cinza-texto">Não respondidas</p>
          </div>
          <div className="flex-1 min-w-24 rounded-botao bg-lavanda p-3 text-center">
            <p className="text-xl font-extrabold font-titulo text-violeta">
              {data.answered_count > 0 ? Math.round(data.passed_count / data.answered_count * 100) : 0}%
            </p>
            <p className="text-xs text-violeta">Aproveitamento</p>
          </div>
        </div>
      </Card>

      {/* Questões */}
      <div className="space-y-3">
        {data.submissions.map(sub => (
          <div key={sub.question_number} className="bg-white rounded-card border-2 border-noite overflow-hidden">
            <div className="flex flex-wrap items-start gap-4 p-5">
              <span className="shrink-0">
                <Tag>Q{sub.question_number}</Tag>
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-cinza-texto line-clamp-2">{sub.statement}</p>
                {sub.submitted_at && (
                  <p className="text-xs text-cinza-texto mt-1">{formatDate(sub.submitted_at)}</p>
                )}
                {sub.cluster_dominant_error && (
                  <Link
                    to={`/exam/${id}/questions/${sub.question_number}?tab=cluster`}
                    className="inline-flex items-center gap-1 mt-1.5 text-xs font-bold px-2 py-0.5 rounded-tag bg-lavanda text-violeta hover:bg-violeta hover:text-white"
                    title="Ver os grupos de dificuldade desta questão"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />
                    Grupo: {sub.cluster_dominant_error}{sub.cluster_size ? ` (${sub.cluster_size})` : ''}
                  </Link>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Badge color={diagColor(sub)}>{diagLabel(sub)}</Badge>
                {sub.submission_id && (
                  <Botao variante="secundario" onClick={() => toggle(sub.question_number)}>
                    {expanded[sub.question_number] ? 'Ocultar' : 'Ver código'}
                  </Botao>
                )}
              </div>
            </div>

            {!sub.submission_id && (
              <div className="px-5 pb-4">
                <p className="text-xs text-cinza-texto italic">Questão não respondida por este aluno.</p>
              </div>
            )}

            {sub.submission_id && expanded[sub.question_number] && (
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

                {sub.pedagogical_diagnosis && (
                  <div className="px-5 py-3 border-t-2 border-noite/10">
                    <p className="text-xs font-bold text-cinza-texto mb-1">Diagnóstico</p>
                    <p className="text-sm text-cinza-texto">{sub.pedagogical_diagnosis}</p>
                    {sub.actionable_feedback && (
                      <div className="mt-2 rounded-botao bg-lavanda px-3 py-2">
                        <p className="text-xs text-violeta">{sub.actionable_feedback}</p>
                      </div>
                    )}
                  </div>
                )}

                {sub.test_results.length > 0 && (
                  <div className="px-5 py-3 border-t-2 border-noite/10">
                    <p className="text-xs font-bold text-cinza-texto mb-2">Testes</p>
                    <div className="space-y-1.5">
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
    </div>
  )
}
