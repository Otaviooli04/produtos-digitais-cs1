import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getEffortReport, getResults } from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import WhoList from '../components/WhoList'
import { shortError } from '../utils/errorLabels'

const ERROR_COLORS = [
  '#7c3aed', '#0ea5e9', '#10b981', '#f59e0b',
  '#ef4444', '#8b5cf6', '#06b6d4', '#f97316',
]

const fmtCase = (s) => (s ? s.replace(/\n/g, '⏎') : '(vazia)')

// Seção delimitada dentro do card, com separador no topo (exceto a primeira).
function Section({ title, hint, children }) {
  return (
    <div className="pt-5 mt-5 border-t border-noite/10">
      <div className="flex items-baseline gap-2 mb-3">
        <h3 className="text-xs font-semibold text-cinza-texto uppercase tracking-wide">{title}</h3>
        {hint && <span className="text-xs text-cinza-texto">{hint}</span>}
      </div>
      {children}
    </div>
  )
}

function Chevron({ open }) {
  return (
    <svg className={`w-3.5 h-3.5 shrink-0 text-cinza-texto/60 group-hover:text-violeta transition-all ${open ? 'rotate-180' : ''}`}
      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  )
}

export default function ResultsPage() {
  const { id } = useParams()
  const [data, setData] = useState(null)
  const [esforco, setEsforco] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState({})
  const [openRow, setOpenRow] = useState({})

  useEffect(() => {
    Promise.all([getResults(id), getEffortReport(id).catch(() => null)])
      .then(([res, rel]) => {
        setData(res.data)
        if (rel) setEsforco(rel.data)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>
  if (!data) return <p className="text-sm text-erro">Erro ao carregar resultados.</p>

  const toggle = (num) => setExpanded(e => ({ ...e, [num]: !e[num] }))
  const toggleRow = (key) => setOpenRow(o => ({ ...o, [key]: !o[key] }))

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-cinza-texto mb-6">
        <Link to={`/exam/${id}`} className="hover:text-cinza-texto">Atividade #{id}</Link>
        <span>›</span>
        <span className="text-cinza-texto">Resultados</span>
      </div>

      <h1 className="text-xl font-semibold text-noite mb-6">Resultados de {data.titulo || data.filename}</h1>

      {esforco && esforco.total_submissoes > 0 && (
        <div className="mb-6 bg-white rounded-xl border border-noite/20 p-5">
          <h2 className="text-sm font-semibold text-noite">Esforço de correção</h2>
          <p className="text-xs text-cinza-texto mt-0.5">
            Submissões agrupadas por sintoma: você revisa uma vez por dificuldade, não uma vez por aluno.
          </p>
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-cinza-texto uppercase tracking-wide">Submissões</p>
              <p className="text-2xl font-bold text-noite">{esforco.total_submissoes}</p>
            </div>
            <div>
              <p className="text-xs text-cinza-texto uppercase tracking-wide">Itens a revisar</p>
              <p className="text-2xl font-bold text-noite">{esforco.itens_a_revisar}</p>
            </div>
            <div>
              <p className="text-xs text-cinza-texto uppercase tracking-wide">Redução</p>
              <p className="text-2xl font-bold text-violeta">
                {esforco.fator_reducao ? `${esforco.fator_reducao}×` : '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-cinza-texto uppercase tracking-wide">Tempo poupado</p>
              <p className="text-2xl font-bold text-noite">
                {Math.round(esforco.minutos_economizados / 6) / 10}h
              </p>
              <p className="text-xs text-cinza-texto">
                estimando {esforco.minutos_por_item} min por item
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-5">
        {data.questions.map((q) => {
          const passRate = q.total_submissions > 0
            ? Math.round((q.passed_count / q.total_submissions) * 100)
            : 0

          const maxErr = Math.max(1, ...q.error_distribution.map(e => e.count))

          return (
            <div key={q.question_number} className="bg-white rounded-xl border border-noite/20">
              <div className="p-5">
                {/* Cabeçalho da questão */}
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-semibold text-violeta bg-lavanda px-2 py-0.5 rounded-md">
                        Q{q.question_number}
                      </span>
                      <Badge color={passRate >= 70 ? 'green' : passRate >= 40 ? 'yellow' : 'red'}>
                        {passRate}% corretos
                      </Badge>
                    </div>
                    <p className="text-sm text-cinza-texto line-clamp-2">{q.statement}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-2xl font-bold text-noite">{q.total_submissions}</p>
                    <p className="text-xs text-cinza-texto">submissões</p>
                  </div>
                </div>

                {/* Aproveitamento */}
                <div className="flex items-center gap-2 mb-1.5 text-xs text-cinza-texto">
                  <span><span className="font-medium text-cinza-texto">{q.passed_count}</span> de {q.total_submissions} corretas</span>
                  {q.partial_count > 0 && (
                    <span className="text-aviso">· {q.partial_count} quase lá</span>
                  )}
                </div>
                <div className="w-full bg-lavanda rounded-full h-2 overflow-hidden">
                  <div className="h-full rounded-full bg-violeta transition-all" style={{ width: `${passRate}%` }} />
                </div>

                {/* Distribuição de erros — expandir mostra QUAIS alunos */}
                {q.error_distribution.length > 0 && (
                  <Section title="Distribuição de erros" hint={`${q.total_submissions - q.passed_count} incorretas`}>
                    <div className="space-y-3">
                      {q.error_distribution.map((e, i) => {
                        const key = `${q.question_number}:e:${i}`
                        const open = !!openRow[key]
                        return (
                          <div key={key}>
                            <button onClick={() => toggleRow(key)} className="w-full flex items-center gap-3 text-xs group">
                              <span className="w-28 shrink-0 truncate text-left text-cinza-texto group-hover:text-noite" title={e.error_category}>
                                {shortError(e.error_category)}
                              </span>
                              <div className="flex-1 bg-lavanda rounded-full h-2.5 overflow-hidden">
                                <div className="h-full rounded-full" style={{ width: `${(e.count / maxErr) * 100}%`, backgroundColor: ERROR_COLORS[i % ERROR_COLORS.length] }} />
                              </div>
                              <span className="w-10 shrink-0 text-right font-medium text-cinza-texto">{e.count}</span>
                              <Chevron open={open} />
                            </button>
                            {open && (
                              <div className="mt-2 ml-28 pl-3 border-l-2 border-noite/10">
                                <WhoList examId={id} matriculas={e.matriculas} />
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </Section>
                )}

                {/* Casos de teste que mais falham — expandir mostra QUEM falhou */}
                {q.testcase_stats.length > 0 && (
                  <Section title="Casos de teste que mais falham">
                    <div className="space-y-3">
                      {q.testcase_stats.map((tc, i) => {
                        const key = `${q.question_number}:t:${i}`
                        const open = !!openRow[key]
                        const barColor = tc.fail_rate >= 60 ? 'bg-erro' : tc.fail_rate >= 30 ? 'bg-aviso' : 'bg-sucesso'
                        return (
                          <div key={key}>
                            <button onClick={() => toggleRow(key)} className="w-full flex items-center gap-3 text-xs group">
                              <span className="flex-1 min-w-0 text-left font-mono text-cinza-texto truncate" title={`entrada: ${tc.input || '(vazia)'}\nesperado: ${tc.expected_output}`}>
                                <span className="text-cinza-texto">in:</span> {fmtCase(tc.input)}
                                <span className="text-cinza-texto"> → </span>{fmtCase(tc.expected_output)}
                              </span>
                              <div className="w-20 shrink-0 bg-lavanda rounded-full h-2.5 overflow-hidden">
                                <div className={`h-full rounded-full ${barColor}`} style={{ width: `${tc.fail_rate}%` }} />
                              </div>
                              <span className="w-20 shrink-0 text-right text-cinza-texto">
                                <span className="font-medium text-cinza-texto">{tc.failed}</span>/{tc.total} ({tc.fail_rate}%)
                              </span>
                              <Chevron open={open} />
                            </button>
                            {open && (
                              <div className="mt-2 pl-3 border-l-2 border-noite/10">
                                <WhoList examId={id} matriculas={tc.failed_matriculas} />
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </Section>
                )}

                {/* Erros de compilação comuns — expandir mostra QUAIS alunos */}
                {q.compile_errors.length > 0 && (
                  <Section title="Erros de compilação comuns">
                    <div className="space-y-3">
                      {q.compile_errors.map((ce, i) => {
                        const key = `${q.question_number}:c:${i}`
                        const open = !!openRow[key]
                        return (
                          <div key={key}>
                            <button onClick={() => toggleRow(key)} className="w-full flex items-start gap-2 text-xs text-left group">
                              <span className="shrink-0 font-medium text-erro bg-erro-fundo border border-erro/15 rounded px-1.5 py-0.5">{ce.count}×</span>
                              <code className="flex-1 text-cinza-texto break-all">{ce.message}</code>
                              <Chevron open={open} />
                            </button>
                            {open && (
                              <div className="mt-2 pl-3 border-l-2 border-noite/10">
                                <WhoList examId={id} matriculas={ce.matriculas} />
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </Section>
                )}
              </div>

              {/* Submissões individuais */}
              {q.submissions.length > 0 && (
                <div className="border-t border-noite/10">
                  <button
                    onClick={() => toggle(q.question_number)}
                    className="w-full flex items-center justify-between px-5 py-3 text-xs text-cinza-texto hover:text-cinza-texto hover:bg-lavanda transition-colors"
                  >
                    <span>Ver submissões individuais ({q.submissions.length})</span>
                    <svg className={`w-4 h-4 transition-transform ${expanded[q.question_number] ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {expanded[q.question_number] && (
                    <div className="divide-y divide-noite/10">
                      {q.submissions.map((s) => {
                        const RowTag = s.matricula ? Link : 'div'
                        const rowProps = s.matricula
                          ? { to: `/exam/${id}/students/${s.matricula}`, className: 'block px-5 py-3 hover:bg-lavanda transition-colors group' }
                          : { className: 'px-5 py-3' }
                        return (
                          <RowTag key={s.id} {...rowProps}>
                            <div className="flex items-center gap-2 mb-1">
                              <Badge color={s.all_tests_passed ? 'green' : s.compile_error ? 'red' : 'yellow'}>
                                {s.all_tests_passed ? 'Correto' : s.compile_error ? 'Erro compilação' : s.diagnosis.error_category}
                              </Badge>
                              {s.matricula && (
                                <span className="text-xs font-medium text-cinza-texto group-hover:text-violeta transition-colors">{s.matricula}</span>
                              )}
                              {!s.all_tests_passed && s.tests_total > 0 && (
                                <span className="text-xs text-cinza-texto">{s.tests_passed}/{s.tests_total} casos</span>
                              )}
                              <span className="text-xs text-cinza-texto">{new Date(s.submitted_at).toLocaleString('pt-BR')}</span>
                              {s.matricula && (
                                <svg className="w-3.5 h-3.5 text-cinza-texto/60 ml-auto group-hover:text-violeta transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                                </svg>
                              )}
                            </div>
                            <p className="text-xs text-cinza-texto">{s.diagnosis.pedagogical_diagnosis}</p>
                          </RowTag>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
