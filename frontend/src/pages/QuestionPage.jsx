import { useEffect, useState } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { ChevronDown, ChevronRight, Plus } from 'lucide-react'
import {
  getExam, getQuestionSubmissions, getGroups, runClustering, runInsights, salvarRespostaDoGrupo,
  deleteSubmission, reevaluateSubmission,
} from '../api/exam'
import ConfirmDialog from '../components/ConfirmDialog'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import BarList from '../components/BarList'
import CodeBlock from '../components/CodeBlock'
import ListControls from '../components/ListControls'
import { shortError } from '../utils/errorLabels'
import { compileErrorLines } from '../utils/highlightLines'
import { formatRelativo } from '../utils/atividade'
import RespostaAoGrupo from '../components/RespostaAoGrupo'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import Progresso from '../components/ui/Progresso'
import RotuloSecao from '../components/ui/RotuloSecao'
import { CORES_CATEGORICAS } from '../utils/coresGraficos'

const SUB_SORTS = [
  { value: 'situacao', label: 'Situação' },
  { value: 'matricula', label: 'Matrícula' },
  { value: 'recentes', label: 'Mais recentes' },
]

// O agrupamento roda sozinho com a estratégia comportamental; o professor não
// escolhe features, vê os grupos já digeridos.
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
  const [openCode, setOpenCode] = useState({})
  const [autoInsightTried, setAutoInsightTried] = useState(false)

  useEffect(() => {
    getExam(id).then(({ data }) => {
      setQuestion(data.questions.find(q => q.number === num))
    })
  }, [id, num])

  useEffect(() => {
    if (tab === 'respostas' && !submissions) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- carga disparada pela troca de aba
      setSubLoading(true)
      getQuestionSubmissions(id, num)
        .then(({ data }) => setSubmissions(data.submissions))
        .finally(() => setSubLoading(false))
    }
  }, [tab, id, num]) // eslint-disable-line react-hooks/exhaustive-deps

  // Carrega os grupos já salvos (agrupados automaticamente no lote) ao abrir a aba.
  useEffect(() => {
    if (tab === 'cluster' && !clusterResult && !groupsFetched) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- carga disparada pela troca de aba
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
          color: CORES_CATEGORICAS[i % CORES_CATEGORICAS.length],
        }))
    : []

  // Re-agrupa agora. Desde que o agrupamento roda a cada envio, isto é um botão
  // de garantia, não o caminho normal. A tela é remontada a partir do GET, e não
  // da resposta do POST, porque só o GET traz a lista de alunos do grupo, os
  // insights e as respostas escritas pelo professor — que sobrevivem ao
  // re-agrupamento, ancoradas na chave estável do grupo.
  const runClusterOnly = async () => {
    setGroupsRunning(true)
    setGroupsError('')
    try {
      await runClustering(id, num)
      const { data } = await getGroups(id, num)
      if (data.has_groups) {
        setClusterResult(data)
        setInsights(data.insights || [])
      }
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
  const respostaFor = (cid) => insights?.find(x => x.cluster_id === cid)?.resposta_professor || ''
  const respostaEmFor = (cid) => insights?.find(x => x.cluster_id === cid)?.resposta_em || null

  // Grava e atualiza só a linha mexida, para a tela não recarregar tudo.
  const salvarResposta = async (clusterId, texto) => {
    const { data } = await salvarRespostaDoGrupo(id, num, clusterId, texto)
    setInsights(atual => (atual || []).map(x => (
      x.cluster_id === clusterId
        ? { ...x, resposta_professor: data.resposta_professor || '', resposta_em: data.resposta_em }
        : x
    )))
  }
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
    return CORES_CATEGORICAS[(idx < 0 ? 0 : idx) % CORES_CATEGORICAS.length]
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

  // A lista de quem caiu no grupo vem pronta do servidor, montada a partir do
  // `cluster_id` da submissão. Antes ela era derivada das coordenadas do gráfico,
  // e quem não tinha coordenada ficava no grupo certo e invisível aqui.
  const alunosByCluster = (cluster_id) =>
    clusterResult?.clusters?.find(c => c.cluster_id === cluster_id)?.alunos ?? []

  // Preenche a descrição dos cartões automaticamente: se há grupos mas nenhum
  // insight salvo, gera uma vez ao abrir a aba (depois vem tudo do cache). Falha
  // (ex.: 429) cai no estado atual — cartão sem texto — e não re-dispara.
  useEffect(() => {
    if (
      tab === 'cluster' && clusterResult && !groupsLoading &&
      !hasInsights && !insightsRunning && !autoInsightTried && rankedGroups.length > 0
    ) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- marca a tentativa automática uma vez só
      setAutoInsightTried(true)
      genInsights()
    }
  }, [tab, clusterResult, groupsLoading, hasInsights, insightsRunning, autoInsightTried, rankedGroups.length]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto mb-6 lg:hidden">
        <Link to={`/exam/${id}`} className="hover:text-noite">Atividade #{id}</Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
      </div>

      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-3 mb-1">
          <h1 className="titulo-pagina">Questão {num}</h1>
          <Botao variante="secundario" to={`/exam/${id}/questions/${num}/testcases`} className="min-h-9! px-3.5! text-[13px]!">
            <Plus className="w-4 h-4" aria-hidden="true" />
            Test cases
          </Botao>
        </div>
        {question && <p className="text-sm text-cinza-texto mt-1 break-words">{question.statement}</p>}
      </div>

      <div className="flex flex-wrap gap-1 border-b-2 border-noite mb-6">
        {TABS.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`min-h-11 px-4 text-sm font-bold border-b-[3px] -mb-[2px] whitespace-nowrap ${
              tab === t.key
                ? 'border-violeta text-violeta'
                : 'border-transparent text-cinza-texto hover:text-noite'
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
              <Spinner className="w-6 h-6 text-violeta" />
            </div>
          )}
          {!subLoading && submissions?.length === 0 && (
            <p className="text-sm text-cinza-texto text-center py-12">Nenhuma submissão ainda.</p>
          )}
          {submissions && submissions.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <Badge color="purple">{submissions.length} submissão{submissions.length !== 1 ? 'ões' : ''}</Badge>
                <Badge color={passRate >= 70 ? 'green' : passRate >= 40 ? 'yellow' : 'red'}>
                  {passRate}% corretos
                </Badge>
              </div>

              <Progresso valor={passRate} rotulo="Respostas corretas" />

              {errorDist.length > 0 && (
                <Card>
                  <RotuloSecao as="h2">Distribuição de erros</RotuloSecao>
                  <BarList items={errorDist} />
                </Card>
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
                <p className="text-sm text-cinza-texto text-center py-8">Nenhuma resposta corresponde à busca.</p>
              )}

              {visibleSubs.length > 0 && (
              <Card className="p-0! gap-0! divide-y-2 divide-noite/10">
                {visibleSubs.map(s => (
                  <div key={s.id} className="p-4">
                    <div
                      className="flex flex-wrap items-center gap-2 cursor-pointer"
                      onClick={() => setExpanded(e => ({ ...e, [s.id]: !e[s.id] }))}
                    >
                      <Badge color={s.all_tests_passed ? 'green' : s.compile_error ? 'red' : 'yellow'}>
                        {s.all_tests_passed ? 'Correto' : s.compile_error ? 'Erro compilação' : s.error_category || 'Parcial'}
                      </Badge>
                      {s.matricula && (
                        <span className="text-xs font-bold text-cinza-texto">{s.matricula}</span>
                      )}
                      <span className="text-xs text-cinza-texto ml-auto">
                        {new Date(s.submitted_at).toLocaleString('pt-BR')}
                      </span>
                      <ChevronDown
                        className={`w-4 h-4 text-cinza-texto transition-transform ${expanded[s.id] ? 'rotate-180' : ''}`}
                        aria-hidden="true"
                      />
                    </div>
                    {expanded[s.id] && (
                      <div className="mt-3 space-y-2">
                        {s.pedagogical_diagnosis && (
                          <p className="text-xs text-cinza-texto">{s.pedagogical_diagnosis}</p>
                        )}
                        {s.actionable_feedback && (
                          <p className="text-xs text-cinza-texto italic">{s.actionable_feedback}</p>
                        )}
                        <CodeBlock code={s.code} highlight={compileErrorLines(s.compile_error, s.code)} />
                        {s.compile_error && (
                          <pre className="text-xs font-mono bg-erro-fundo rounded-botao border-2 border-erro p-3 text-erro overflow-x-auto whitespace-pre-wrap">
                            {s.compile_error}
                          </pre>
                        )}
                        <div className="flex flex-wrap gap-2 pt-1">
                          <Botao
                            variante="secundario"
                            onClick={() => handleReevaluate(s.id)}
                            disabled={reevaluatingId === s.id}
                            className="min-h-9! px-3.5! text-[13px]!"
                          >
                            {reevaluatingId === s.id && <Spinner className="w-3 h-3" />}
                            Reavaliar
                          </Botao>
                          <Botao variante="perigo" onClick={() => setDeleteSub(s)} className="min-h-9! px-3.5! text-[13px]!">
                            Excluir
                          </Botao>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </Card>
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
              <Spinner className="w-6 h-6 text-violeta" />
            </div>
          )}

          {!clusterResult && !groupsLoading && (
            <Card>
              <p className="text-sm text-cinza-texto">
                Os grupos de dificuldade são calculados automaticamente ao enviar as submissões
                em lote. Esta questão ainda não tem grupos — você pode gerá-los agora.
              </p>
              <div>
                <Botao onClick={runClusterOnly} disabled={groupsRunning}>
                  {groupsRunning && <Spinner className="w-4 h-4" />}
                  {groupsRunning ? 'Analisando…' : 'Analisar grupos de dificuldade'}
                </Botao>
              </div>
            </Card>
          )}

          {groupsError && (
            <div className="rounded-botao bg-erro-fundo border-2 border-erro px-4 py-3 text-sm text-erro">
              {groupsError}
            </div>
          )}

          {clusterResult && (
            <>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                  <p className="text-sm text-cinza-texto">
                    {rankedGroups.length} grupo{rankedGroups.length !== 1 ? 's' : ''} em {clusterResult.total_submissions} submissões
                  </p>
                  {clusterResult.atualizado_em && (
                    <p className="text-xs text-cinza-texto mt-0.5">
                      Agrupado {formatRelativo(clusterResult.atualizado_em)}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {!hasInsights && (
                    <Botao
                      onClick={genInsights}
                      disabled={insightsRunning}
                      className="min-h-9! px-3.5! text-[13px]!"
                    >
                      {insightsRunning && <Spinner className="w-3 h-3" />}
                      {insightsRunning ? 'Gerando…' : 'Gerar intervenção (Gemini)'}
                    </Botao>
                  )}
                  <Botao
                    variante="secundario"
                    onClick={runClusterOnly}
                    disabled={groupsRunning}
                    className="min-h-9! px-3.5! text-[13px]!"
                  >
                    {groupsRunning && <Spinner className="w-3 h-3" />}
                    Recalcular
                  </Botao>
                </div>
              </div>

              <div className="space-y-5">
                {rankedGroups.map(c => {
                  const alunos = alunosByCluster(c.cluster_id)
                  const pct = clusterResult.total_submissions
                    ? Math.round((c.size / clusterResult.total_submissions) * 100)
                    : 0
                  const insight = insightFor(c.cluster_id)
                  const hot = highlightFor(c.cluster_id)
                  return (
                    <Card key={c.cluster_id} principal className="gap-0!">
                      <div className="flex flex-wrap items-center gap-2 mb-3">
                        <span className="w-4 h-4 rounded-full shrink-0 border-2 border-noite" style={{ backgroundColor: clusterColor(c.cluster_id) }} aria-hidden="true" />
                        <Badge color={isCorrect(c.dominant_error) ? 'green' : 'red'}>{c.dominant_error}</Badge>
                        {c.failing_label && <span className="text-xs text-cinza-texto">· {c.failing_label}</span>}
                        <span className="ml-auto text-xs text-cinza-texto">{c.size} aluno{c.size !== 1 ? 's' : ''} · {pct}%</span>
                      </div>

                      {insight && (
                        <div className="flex gap-2 mb-3">
                          <div className="w-0.5 bg-violeta/30 rounded-full shrink-0" />
                          <p className="text-sm text-cinza-texto leading-relaxed break-words min-w-0">{insight}</p>
                        </div>
                      )}

                      {!insight && insightsRunning && (
                        <div className="flex items-center gap-2 mb-3 text-xs text-cinza-texto">
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
                              className="text-xs bg-lavanda text-cinza-texto px-2 py-0.5 rounded-tag font-mono hover:text-violeta transition-colors"
                            >
                              {m}
                            </Link>
                          ))}
                        </div>
                      )}

                      <RespostaAoGrupo
                        resposta={respostaFor(c.cluster_id)}
                        respostaEm={respostaEmFor(c.cluster_id)}
                        insight={insight}
                        alunos={c.size}
                        onSave={(texto) => salvarResposta(c.cluster_id, texto)}
                      />

                      {c.representative_code && (
                        <div className="mt-3">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setOpenCode(o => ({ ...o, [c.cluster_id]: !o[c.cluster_id] }))}
                              className="min-h-11 text-xs font-bold text-cinza-texto hover:text-noite transition-colors"
                            >
                              {openCode[c.cluster_id] ? '− Ocultar' : '+ Ver'} código representativo
                            </button>
                            {hot.length > 0 && (
                              <span className="text-xs text-erro">
                                · {hot.length === 1 ? `linha ${hot[0]}` : `linhas ${hot.join(', ')}`} em destaque
                              </span>
                            )}
                            {c.representative_matricula && (
                              <span className="text-xs text-cinza-texto">
                                · de{' '}
                                <Link
                                  to={`/exam/${id}/students/${c.representative_matricula}`}
                                  className="font-mono text-cinza-texto hover:text-violeta transition-colors break-all"
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
                    </Card>
                  )
                })}
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
