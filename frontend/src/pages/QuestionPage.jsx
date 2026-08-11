import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import {
  getExam, getQuestionSubmissions, getGroups, runClustering, runInsights,
  deleteSubmission, reevaluateSubmission,
} from '../api/exam'
import ConfirmDialog from '../components/ConfirmDialog'
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import BarList from '../components/BarList'
import CodeBlock from '../components/CodeBlock'
import ListControls from '../components/ListControls'
import { shortError } from '../utils/errorLabels'
import { compileErrorLines } from '../utils/highlightLines'

const SUB_SORTS = [
  { value: 'situacao', label: 'Situação' },
  { value: 'matricula', label: 'Matrícula' },
  { value: 'recentes', label: 'Mais recentes' },
]

const CLUSTER_COLORS = ['#7c3aed', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']
const ERROR_COLORS = ['#7c3aed', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316']
// O agrupamento roda sozinho com a estratégia comportamental; o professor não
// escolhe features, vê os grupos já digeridos.
const GROUP_STRATEGY = 'tfidf_behavioral'
const TABS = [
  { key: 'respostas', label: 'Respostas' },
  { key: 'cluster', label: 'Grupos de dificuldade' },
]

export default function QuestionPage() {
  const { id, num } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'respostas'

  const [question, setQuestion] = useState(null)

  // Respostas
  const [submissions, setSubmissions] = useState(null)
  const [subLoading, setSubLoading] = useState(false)
  const [expanded, setExpanded] = useState({})
  const [subSearch, setSubSearch] = useState('')
  const [subSort, setSubSort] = useState('situacao')
  const [deleteSub, setDeleteSub] = useState(null)
  const [busySub, setBusySub] = useState(false)
  const [reevaluatingId, setReevaluatingId] = useState(null)

  const reloadSubs = () =>
    getQuestionSubmissions(id, num).then(({ data }) => setSubmissions(data.submissions))

  const handleReevaluate = async (subId) => {
    setReevaluatingId(subId)
    try {
      await reevaluateSubmission(subId)
      await reloadSubs()
    } catch { /* mantém estado */ } finally {
      setReevaluatingId(null)
    }
  }

  const confirmDeleteSub = async () => {
    setBusySub(true)
    try {
      await deleteSubmission(deleteSub.id)
      setSubmissions(prev => prev.filter(s => s.id !== deleteSub.id))
      setDeleteSub(null)
    } catch { /* mantém */ } finally {
      setBusySub(false)
    }
  }

  // Grupos de dificuldade. O agrupamento roda automático no fim do lote; aqui a aba
  // só CARREGA o que já existe. Recalcular re-agrupa; a intervenção (LLM) é sob demanda.
  const [groupsLoading, setGroupsLoading] = useState(false)
  const [groupsFetched, setGroupsFetched] = useState(false)
  const [groupsRunning, setGroupsRunning] = useState(false)
  const [insightsRunning, setInsightsRunning] = useState(false)
  const [clusterResult, setClusterResult] = useState(null)
  const [insights, setInsights] = useState(null)
  const [groupsError, setGroupsError] = useState('')
  const [techOpen, setTechOpen] = useState(false)
  const [openCode, setOpenCode] = useState({})
  const [autoInsightTried, setAutoInsightTried] = useState(false)

  useEffect(() => {
    getExam(id).then(({ data }) => {
      setQuestion(data.questions.find(q => q.number === num))
    })
  }, [id, num])

  useEffect(() => {
    if (tab === 'respostas' && !submissions) {
      setSubLoading(true)
      getQuestionSubmissions(id, num)
        .then(({ data }) => setSubmissions(data.submissions))
        .finally(() => setSubLoading(false))
    }
  }, [tab, id, num]) // eslint-disable-line react-hooks/exhaustive-deps

  // Carrega os grupos já salvos (agrupados automaticamente no lote) ao abrir a aba.
  useEffect(() => {
    if (tab === 'cluster' && !clusterResult && !groupsFetched) {
      setGroupsFetched(true)
      setGroupsLoading(true)
      getGroups(id, num)
        .then(({ data }) => {
          if (data.has_groups) {
            setClusterResult(data)
            setInsights(data.insights || [])
          }
        })
        .catch(() => { /* sem grupos ainda */ })
        .finally(() => setGroupsLoading(false))
    }
  }, [tab, id, num, clusterResult, groupsFetched])

  const setTab = (key) => setSearchParams({ tab: key })

  const passRate = submissions && submissions.length > 0
    ? Math.round((submissions.filter(s => s.all_tests_passed).length / submissions.length) * 100)
    : 0

  const errorDist = submissions
    ? Object.entries(
        submissions.reduce((acc, s) => {
          const cat = s.error_category || 'desconhecido'
          acc[cat] = (acc[cat] || 0) + 1
          return acc
        }, {})
      ).map(([error_category, count]) => ({ error_category, count }))
        .sort((a, b) => b.count - a.count)
        .map(({ error_category, count }, i) => ({
          label: shortError(error_category),
          title: error_category,
          value: count,
          color: ERROR_COLORS[i % ERROR_COLORS.length],
        }))
    : []

  // Agrupa (ou re-agrupa). Barato, sem LLM. Re-agrupar invalida os insights antigos.
  const runClusterOnly = async () => {
    setGroupsRunning(true)
    setGroupsError('')
    try {
      const { data } = await runClustering(id, num, GROUP_STRATEGY)
      setClusterResult(data)
      setInsights([])
      setAutoInsightTried(false)
    } catch (e) {
      setGroupsError(e.response?.data?.detail || 'Erro ao analisar os grupos.')
    } finally {
      setGroupsRunning(false)
    }
  }

  // Intervenção pedagógica do Gemini, sob demanda (custa uma chamada por questão).
  const genInsights = async () => {
    setInsightsRunning(true)
    setGroupsError('')
    try {
      const { data } = await runInsights(id, num)
      setInsights(data.insights)
    } catch (e) {
      setGroupsError(e.response?.data?.detail || 'Erro ao gerar a intervenção pedagógica.')
    } finally {
      setInsightsRunning(false)
    }
  }

  const hasInsights = insights?.some(x => x.insight)
  const isCorrect = (err) => /correto/i.test(err || '')
  const insightFor = (cid) => insights?.find(x => x.cluster_id === cid)?.insight || ''
  // Linhas problemáticas do código representativo (mesmo canal dos insights).
  const highlightFor = (cid) => insights?.find(x => x.cluster_id === cid)?.highlight_lines || []

  // Situação da submissão (rótulo único p/ filtrar e ordenar a aba Respostas).
  const subStatus = (s) =>
    s.all_tests_passed ? 'Correto' : s.compile_error ? 'Erro de Compilação' : (s.error_category || 'Parcial')

  // Lista de Respostas filtrada (matrícula/situação) e ordenada conforme o controle.
  const visibleSubs = (submissions || [])
    .filter(s => {
      const q = subSearch.trim().toLowerCase()
      if (!q) return true
      return (s.matricula || '').toLowerCase().includes(q) || subStatus(s).toLowerCase().includes(q)
    })
    .sort((a, b) => {
      if (subSort === 'matricula')
        return (a.matricula || '').localeCompare(b.matricula || '', 'pt', { numeric: true })
      if (subSort === 'recentes')
        return new Date(b.submitted_at) - new Date(a.submitted_at)
      // 'situacao': corretos por último; erros agrupados por categoria; depois matrícula.
      const ca = isCorrect(subStatus(a)), cb = isCorrect(subStatus(b))
      if (ca !== cb) return ca ? 1 : -1
      const la = subStatus(a), lb = subStatus(b)
      if (la !== lb) return la.localeCompare(lb, 'pt')
      return (a.matricula || '').localeCompare(b.matricula || '', 'pt', { numeric: true })
    })

  // Cor estável por grupo (ordem original dos clusters) p/ casar cartão e scatter.
  const clusterColor = (cid) => {
    const idx = clusterResult?.clusters.findIndex(c => c.cluster_id === cid) ?? -1
    return CLUSTER_COLORS[(idx < 0 ? 0 : idx) % CLUSTER_COLORS.length]
  }

  // Cartões ranqueados por SEVERIDADE: mais casos de teste falhos primeiro
  // (dificuldade mais grave no topo); "Correto" sempre por último; grupos sem
  // assinatura coesa (failing_count nulo) ao fim das dificuldades; desempate por
  // tamanho. Ruído (-1) fica fora.
  const rankedGroups = clusterResult
    ? [...clusterResult.clusters]
        .filter(c => c.cluster_id !== -1)
        .sort((a, b) => {
          if (isCorrect(a.dominant_error) !== isCorrect(b.dominant_error))
            return isCorrect(a.dominant_error) ? 1 : -1
          const fa = a.failing_count ?? -1
          const fb = b.failing_count ?? -1
          if (fa !== fb) return fb - fa
          return b.size - a.size
        })
    : []

  const scatterByCluster = (c) =>
    clusterResult?.scatter.filter(p => p.cluster_id === c.cluster_id) ?? []

  const alunosByCluster = (cluster_id) =>
    clusterResult?.scatter
      .filter(p => p.cluster_id === cluster_id && p.matricula)
      .map(p => p.matricula) ?? []

  const noisePoints = clusterResult?.scatter.filter(p => p.cluster_id === -1) ?? []

  // Preenche a descrição dos cartões automaticamente: se há grupos mas nenhum
  // insight salvo, gera uma vez ao abrir a aba (depois vem tudo do cache). Falha
  // (ex.: 429) cai no estado atual — cartão sem texto — e não re-dispara.
  useEffect(() => {
    if (
      tab === 'cluster' && clusterResult && !groupsLoading &&
      !hasInsights && !insightsRunning && !autoInsightTried && rankedGroups.length > 0
    ) {
      setAutoInsightTried(true)
      genInsights()
    }
  }, [tab, clusterResult, groupsLoading, hasInsights, insightsRunning, autoInsightTried, rankedGroups.length]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <span className="text-gray-600">Questão {num}</span>
      </div>

      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded-md">Q{num}</span>
          <Link
            to={`/exam/${id}/questions/${num}/testcases`}
            className="text-xs px-2.5 py-1 rounded-md border border-gray-200 text-gray-500 hover:bg-gray-50 transition-colors"
          >
            + Test cases
          </Link>
        </div>
        {question && <p className="text-sm text-gray-700 mt-1">{question.statement}</p>}
      </div>

      <div className="flex gap-1 border-b border-gray-200 mb-6">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === t.key
                ? 'border-purple-600 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab: Respostas */}
      {tab === 'respostas' && (
        <div>
          {subLoading && (
            <div className="flex justify-center py-16">
              <Spinner className="w-6 h-6 text-purple-600" />
            </div>
          )}
          {!subLoading && submissions?.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-12">Nenhuma submissão ainda.</p>
          )}
          {submissions && submissions.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Badge color="purple">{submissions.length} submissão{submissions.length !== 1 ? 'ões' : ''}</Badge>
                <Badge color={passRate >= 70 ? 'green' : passRate >= 40 ? 'yellow' : 'red'}>
                  {passRate}% corretos
                </Badge>
              </div>

              <div className="w-full bg-gray-100 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full bg-purple-500 transition-all"
                  style={{ width: `${passRate}%` }}
                />
              </div>

              {errorDist.length > 0 && (
                <div className="bg-white rounded-xl border border-gray-200 p-5">
                  <p className="text-xs font-medium text-gray-500 mb-3">Distribuição de erros</p>
                  <BarList items={errorDist} />
                </div>
              )}

              <ListControls
                search={subSearch}
                onSearch={setSubSearch}
                sort={subSort}
                onSort={setSubSort}
                sortOptions={SUB_SORTS}
                placeholder="Buscar por matrícula ou situação…"
              />

              {visibleSubs.length === 0 && (
                <p className="text-sm text-gray-500 text-center py-8">Nenhuma resposta corresponde à busca.</p>
              )}

              {visibleSubs.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-50">
                {visibleSubs.map(s => (
                  <div key={s.id} className="p-4">
                    <div
                      className="flex items-center gap-2 cursor-pointer"
                      onClick={() => setExpanded(e => ({ ...e, [s.id]: !e[s.id] }))}
                    >
                      <Badge color={s.all_tests_passed ? 'green' : s.compile_error ? 'red' : 'yellow'}>
                        {s.all_tests_passed ? 'Correto' : s.compile_error ? 'Erro compilação' : s.error_category || 'Parcial'}
                      </Badge>
                      {s.matricula && (
                        <span className="text-xs font-medium text-gray-700">{s.matricula}</span>
                      )}
                      <span className="text-xs text-gray-400 ml-auto">
                        {new Date(s.submitted_at).toLocaleString('pt-BR')}
                      </span>
                      <svg
                        className={`w-4 h-4 text-gray-400 transition-transform ${expanded[s.id] ? 'rotate-180' : ''}`}
                        fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                    {expanded[s.id] && (
                      <div className="mt-3 space-y-2">
                        {s.pedagogical_diagnosis && (
                          <p className="text-xs text-gray-600">{s.pedagogical_diagnosis}</p>
                        )}
                        {s.actionable_feedback && (
                          <p className="text-xs text-gray-500 italic">{s.actionable_feedback}</p>
                        )}
                        <CodeBlock code={s.code} highlight={compileErrorLines(s.compile_error, s.code)} />
                        {s.compile_error && (
                          <pre className="text-xs font-mono bg-red-50 rounded-lg p-3 text-red-600 overflow-x-auto whitespace-pre-wrap">
                            {s.compile_error}
                          </pre>
                        )}
                        <div className="flex gap-2 pt-1">
                          <button
                            onClick={() => handleReevaluate(s.id)}
                            disabled={reevaluatingId === s.id}
                            className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition-colors"
                          >
                            {reevaluatingId === s.id && <Spinner className="w-3 h-3" />}
                            Reavaliar
                          </button>
                          <button
                            onClick={() => setDeleteSub(s)}
                            className="text-xs px-2.5 py-1.5 rounded-md border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
                          >
                            Excluir
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tab: Grupos de dificuldade */}
      {tab === 'cluster' && (
        <div className="space-y-4">
          {!clusterResult && groupsLoading && (
            <div className="flex justify-center py-16">
              <Spinner className="w-6 h-6 text-purple-600" />
            </div>
          )}

          {!clusterResult && !groupsLoading && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-sm text-gray-600 mb-4">
                Os grupos de dificuldade são calculados automaticamente ao enviar as submissões
                em lote. Esta questão ainda não tem grupos — você pode gerá-los agora.
              </p>
              <button
                onClick={runClusterOnly}
                disabled={groupsRunning}
                className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                {groupsRunning && <Spinner className="w-4 h-4" />}
                {groupsRunning ? 'Analisando…' : 'Analisar grupos de dificuldade'}
              </button>
            </div>
          )}

          {groupsError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {groupsError}
            </div>
          )}

          {clusterResult && (
            <>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <p className="text-sm text-gray-500">
                  {rankedGroups.length} grupo{rankedGroups.length !== 1 ? 's' : ''} em {clusterResult.total_submissions} submissões
                </p>
                <div className="flex items-center gap-2">
                  {!hasInsights && (
                    <button
                      onClick={genInsights}
                      disabled={insightsRunning}
                      className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors"
                    >
                      {insightsRunning && <Spinner className="w-3 h-3" />}
                      {insightsRunning ? 'Gerando…' : 'Gerar intervenção (Gemini)'}
                    </button>
                  )}
                  <button
                    onClick={runClusterOnly}
                    disabled={groupsRunning}
                    className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 disabled:opacity-40 transition-colors"
                  >
                    {groupsRunning && <Spinner className="w-3 h-3" />}
                    Recalcular
                  </button>
                </div>
              </div>

              <div className="space-y-3">
                {rankedGroups.map(c => {
                  const alunos = alunosByCluster(c.cluster_id)
                  const pct = clusterResult.total_submissions
                    ? Math.round((c.size / clusterResult.total_submissions) * 100)
                    : 0
                  const insight = insightFor(c.cluster_id)
                  const hot = highlightFor(c.cluster_id)
                  return (
                    <div key={c.cluster_id} className="bg-white rounded-xl border border-gray-200 p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="w-3 h-3 rounded-full shrink-0" style={{ backgroundColor: clusterColor(c.cluster_id) }} />
                        <Badge color={isCorrect(c.dominant_error) ? 'green' : 'red'}>{c.dominant_error}</Badge>
                        {c.failing_label && <span className="text-xs text-gray-500">· {c.failing_label}</span>}
                        <span className="ml-auto text-xs text-gray-400">{c.size} aluno{c.size !== 1 ? 's' : ''} · {pct}%</span>
                      </div>

                      {insight && (
                        <div className="flex gap-2 mb-3">
                          <div className="w-0.5 bg-purple-200 rounded-full shrink-0" />
                          <p className="text-sm text-gray-700 leading-relaxed">{insight}</p>
                        </div>
                      )}

                      {!insight && insightsRunning && (
                        <div className="flex items-center gap-2 mb-3 text-xs text-gray-400">
                          <Spinner className="w-3 h-3" />
                          Gerando descrição…
                        </div>
                      )}

                      {alunos.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {alunos.map(m => (
                            <Link
                              key={m}
                              to={`/exam/${id}/students/${m}`}
                              className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-md font-mono hover:bg-purple-50 hover:text-purple-700 transition-colors"
                            >
                              {m}
                            </Link>
                          ))}
                        </div>
                      )}

                      {c.representative_code && (
                        <div className="mt-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setOpenCode(o => ({ ...o, [c.cluster_id]: !o[c.cluster_id] }))}
                              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
                            >
                              {openCode[c.cluster_id] ? '− Ocultar' : '+ Ver'} código representativo
                            </button>
                            {hot.length > 0 && (
                              <span className="text-xs text-red-500">
                                · {hot.length === 1 ? `linha ${hot[0]}` : `linhas ${hot.join(', ')}`} em destaque
                              </span>
                            )}
                            {c.representative_matricula && (
                              <span className="text-xs text-gray-400">
                                · de{' '}
                                <Link
                                  to={`/exam/${id}/students/${c.representative_matricula}`}
                                  className="font-mono text-gray-500 hover:text-purple-700 transition-colors"
                                >
                                  {c.representative_matricula}
                                </Link>
                              </span>
                            )}
                          </div>
                          {openCode[c.cluster_id] && (
                            <CodeBlock code={c.representative_code} highlight={hot} />
                          )}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Detalhes técnicos (scatter UMAP + métricas) — preservados p/ análise */}
              <div className="bg-white rounded-xl border border-gray-200">
                <button
                  onClick={() => setTechOpen(o => !o)}
                  className="w-full flex items-center justify-between px-5 py-3 text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors rounded-xl"
                >
                  <span>Detalhes técnicos</span>
                  <svg className={`w-4 h-4 transition-transform ${techOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {techOpen && (
                  <div className="px-5 pb-5 space-y-4">
                    <div className="flex items-center gap-3 flex-wrap">
                      <Badge color="purple">{clusterResult.total_submissions} submissões</Badge>
                      <Badge color="gray">{clusterResult.clusters.length} grupos</Badge>
                      {clusterResult.silhouette_score != null && (
                        <Badge color={clusterResult.silhouette_score >= 0.5 ? 'green' : clusterResult.silhouette_score >= 0.25 ? 'yellow' : 'gray'}>
                          Silhouette: {clusterResult.silhouette_score.toFixed(3)}
                        </Badge>
                      )}
                      <Badge color="gray">Estratégia: comportamental</Badge>
                    </div>
                    <div>
                      <h2 className="text-sm font-medium text-gray-700 mb-4">Projeção UMAP 2D</h2>
                      <ResponsiveContainer width="100%" height={360}>
                        <ScatterChart margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                          <XAxis dataKey="x" name="UMAP 1" tick={{ fontSize: 10 }} label={{ value: 'UMAP 1', position: 'insideBottom', offset: -4, fontSize: 10 }} />
                          <YAxis dataKey="y" name="UMAP 2" tick={{ fontSize: 10 }} label={{ value: 'UMAP 2', angle: -90, position: 'insideLeft', fontSize: 10 }} />
                          <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }} formatter={(v, name) => [v.toFixed(3), name]} />
                          <Legend wrapperStyle={{ fontSize: 12 }} />
                          {clusterResult.clusters.map(c => (
                            <Scatter
                              key={c.cluster_id}
                              name={`Grupo ${c.cluster_id} (${c.dominant_error})`}
                              data={scatterByCluster(c)}
                              fill={clusterColor(c.cluster_id)}
                            />
                          ))}
                          {noisePoints.length > 0 && (
                            <Scatter name="Ruído" data={noisePoints} fill="#d1d5db" />
                          )}
                        </ScatterChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}

      <ConfirmDialog
        open={!!deleteSub}
        onClose={() => setDeleteSub(null)}
        onConfirm={confirmDeleteSub}
        loading={busySub}
        title="Excluir submissão"
        confirmLabel="Excluir"
        message={deleteSub
          ? `Excluir a submissão${deleteSub.matricula ? ` de ${deleteSub.matricula}` : ''}? Esta ação não pode ser desfeita.`
          : ''}
      />
    </div>
  )
}
