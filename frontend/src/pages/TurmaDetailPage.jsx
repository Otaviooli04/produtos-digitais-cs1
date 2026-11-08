import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { adicionarListaDeAquecimento, getTurma, getTurmaAnalytics, deleteExam } from '../api/exam'
import Spinner from '../components/Spinner'
import ConfirmDialog from '../components/ConfirmDialog'
import ListControls from '../components/ListControls'
import Badge from '../components/Badge'
import BarList from '../components/BarList'
import TrajetoriaDeErros from '../components/TrajetoriaDeErros'
import FunilDaTurma from '../components/FunilDaTurma'
import { comTipo, modoLabel } from '../utils/atividade'
import { shortError } from '../utils/errorLabels'

const GRUPOS_DE_ATIVIDADE = [
  { modo: 'prova', titulo: 'Provas', vazio: 'Nenhuma prova nesta turma.' },
  { modo: 'treino', titulo: 'Listas', vazio: 'Nenhuma lista nesta turma.' },
]

const contagemPorModo = (exams) => {
  const listas = exams.filter(e => e.modo === 'treino').length
  const provas = exams.length - listas
  return `${provas} prova${provas !== 1 ? 's' : ''} e ${listas} lista${listas !== 1 ? 's' : ''}`
}

const SORT_OPTIONS = [
  { value: 'recent', label: 'Mais recentes' },
  { value: 'oldest', label: 'Mais antigas' },
  { value: 'name', label: 'Nome (A–Z)' },
]

const ERR_COLOR = '#e11d48'
const rateColor = (r) => (r >= 70 ? '#10b981' : r >= 40 ? '#f59e0b' : '#ef4444')

function KpiCard({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-noite/20 p-5 flex flex-col gap-1">
      <p className="text-xs text-cinza-texto font-medium uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-noite">{value ?? '—'}</p>
      {sub && <p className="text-xs text-cinza-texto">{sub}</p>}
    </div>
  )
}

function PassRateBar({ rate }) {
  if (rate == null) return <span className="text-xs text-cinza-texto">sem dados</span>
  const color = rate >= 70 ? 'bg-sucesso' : rate >= 40 ? 'bg-aviso' : 'bg-erro'
  return (
    <div className="flex items-center gap-2 mt-2">
      <div className="flex-1 h-1.5 bg-lavanda rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${rate}%` }} />
      </div>
      <span className="text-xs font-medium text-cinza-texto w-10 text-right">{rate}%</span>
    </div>
  )
}

export default function TurmaDetailPage() {
  const { turmaId } = useParams()
  const navigate = useNavigate()
  const [turma, setTurma] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deleteExamTarget, setDeleteExamTarget] = useState(null)
  const [deletingExam, setDeletingExam] = useState(false)
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('recent')
  const [copiado, setCopiado] = useState(false)
  const [conviteCopiado, setConviteCopiado] = useState(false)
  const [recargaFunil, setRecargaFunil] = useState(0)
  const [adicionandoAquecimento, setAdicionandoAquecimento] = useState(false)
  const [erroAquecimento, setErroAquecimento] = useState('')

  const adicionarAquecimento = async () => {
    setErroAquecimento('')
    setAdicionandoAquecimento(true)
    try {
      const { data } = await adicionarListaDeAquecimento(turmaId)
      navigate(`/exam/${data.exam_id}`)
    } catch {
      setErroAquecimento('Não foi possível adicionar a lista de aquecimento. Tente de novo.')
      setAdicionandoAquecimento(false)
    }
  }

  const copiarCodigo = async () => {
    if (!turma?.codigo_acesso) return
    try {
      await navigator.clipboard.writeText(turma.codigo_acesso)
      setCopiado(true)
      setTimeout(() => setCopiado(false), 2000)
    } catch {
      setError('Não foi possível copiar o código.')
    }
  }

  // RF06: mensagem pronta com o link que já leva o código da turma.
  const copiarConvite = async () => {
    if (!turma?.codigo_acesso) return
    const link = `${window.location.origin}/aluno/convite/${turma.codigo_acesso}`
    const mensagem =
      `Nossa turma de ${turma.nome} vai usar o Analytics CS1 nas listas e no treino. ` +
      `Para entrar, abra ${link} e crie sua conta. ` +
      `Se preferir, use o código ${turma.codigo_acesso} na área do aluno.`
    try {
      await navigator.clipboard.writeText(mensagem)
      setConviteCopiado(true)
      setTimeout(() => setConviteCopiado(false), 2000)
    } catch {
      setError('Não foi possível copiar o convite.')
    }
  }

  const confirmDeleteExam = async () => {
    setDeletingExam(true)
    try {
      await deleteExam(deleteExamTarget.id)
      setTurma(t => ({ ...t, exams: t.exams.filter(e => e.id !== deleteExamTarget.id) }))
      setDeleteExamTarget(null)
      // Rebusca os analytics (agregados no servidor) após remover a prova.
      getTurmaAnalytics(turmaId).then(({ data: a }) => setAnalytics(a)).catch(() => {})
      setRecargaFunil(n => n + 1)
    } catch {
      setError('Erro ao excluir a prova.')
    } finally {
      setDeletingExam(false)
    }
  }

  useEffect(() => {
    Promise.all([getTurma(turmaId), getTurmaAnalytics(turmaId)])
      .then(([{ data: t }, { data: a }]) => {
        setTurma(t)
        setAnalytics(a)
      })
      .catch(() => setError('Erro ao carregar turma.'))
      .finally(() => setLoading(false))
  }, [turmaId])

  const formatDate = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>
  if (error) return <p className="text-erro text-sm">{error}</p>

  const examAnalyticsMap = Object.fromEntries((analytics?.provas ?? []).map(p => [p.id, p]))

  const displayedExams = (turma.exams ?? [])
    .filter(exam => {
      const q = search.trim().toLowerCase()
      return q ? (exam.titulo || exam.filename).toLowerCase().includes(q) : true
    })
    .sort((a, b) => {
      if (sort === 'name')
        return (a.titulo || a.filename).localeCompare(b.titulo || b.filename, 'pt-BR')
      const da = new Date(a.created_at).getTime()
      const db = new Date(b.created_at).getTime()
      return sort === 'oldest' ? da - db : db - da
    })

  const mediaDoModo = (modo) => {
    const taxas = (analytics?.provas ?? [])
      .filter(p => (p.modo || 'prova') === modo && p.pass_rate != null)
      .map(p => p.pass_rate)
    return taxas.length ? `${(taxas.reduce((a, b) => a + b, 0) / taxas.length).toFixed(1)}%` : '—'
  }
  const aproveitamentoPorModo = `provas ${mediaDoModo('prova')} · listas ${mediaDoModo('treino')}`

  const evolucaoData = (analytics?.provas ?? []).map(p => ({
    name: comTipo(p.modo, p.titulo || p.filename.replace(/\.[^.]+$/, '')),
    taxa: p.pass_rate ?? 0,
  }))

  const truncar = (s, n = 14) => (s.length > n ? `${s.slice(0, n)}…` : s)

  const errosData = (analytics?.top_erros ?? []).map(e => ({
    name: shortError(e.error_category),
    full: e.error_category,
    count: e.count,
  }))

  return (
    <div className="space-y-8">
      {/* Breadcrumb + header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-cinza-texto mb-4">
          <Link to="/" className="hover:text-cinza-texto">Turmas</Link>
          <span>›</span>
          <span className="text-cinza-texto">{turma.nome}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold text-noite">{turma.nome}</h1>
            <span className="text-xs font-medium text-violeta bg-lavanda border border-violeta/15 px-2 py-0.5 rounded-md">
              {turma.codigo}
            </span>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-2">
            {!turma.exams.some(e => e.filename === 'lista-de-aquecimento') && (
              <button
                onClick={adicionarAquecimento}
                disabled={adicionandoAquecimento}
                className="text-sm px-3 py-1.5 rounded-lg border border-noite/20 text-cinza-texto hover:bg-lavanda disabled:opacity-50 transition-colors"
              >
                {adicionandoAquecimento ? 'Adicionando...' : 'Adicionar lista de aquecimento'}
              </button>
            )}
          <button
            onClick={() => navigate(`/turma/${turmaId}/upload`)}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-violeta text-white hover:bg-violeta-escuro transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            Nova atividade
          </button>
          </div>
        </div>
        {erroAquecimento && <p className="mt-2 text-right text-xs text-erro">{erroAquecimento}</p>}
      </div>

      {/* Entrada dos alunos na turma */}
      <div className="bg-white rounded-xl border border-noite/20 p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs text-cinza-texto font-medium uppercase tracking-wide">Código de acesso da turma</p>
          <p className="mt-1 text-2xl font-bold font-mono tracking-[0.25em] text-noite">
            {turma.codigo_acesso || '—'}
          </p>
          <p className="text-xs text-cinza-texto mt-1">
            Passe o código ou o convite com link, que já leva o código. {turma.aluno_count ?? 0} já {(turma.aluno_count ?? 0) === 1 ? 'entrou' : 'entraram'} com conta.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={copiarCodigo}
            disabled={!turma.codigo_acesso}
            className="text-sm px-3 py-1.5 rounded-lg border border-noite/20 text-cinza-texto hover:bg-lavanda disabled:opacity-40 transition-colors"
          >
            {copiado ? 'Copiado' : 'Copiar código'}
          </button>
          <button
            onClick={copiarConvite}
            disabled={!turma.codigo_acesso}
            className="text-sm px-3 py-1.5 rounded-lg border border-noite/20 text-cinza-texto hover:bg-lavanda disabled:opacity-40 transition-colors"
          >
            {conviteCopiado ? 'Copiado' : 'Copiar convite'}
          </button>
          <Link
            to="/aluno/login"
            target="_blank"
            className="text-sm px-3 py-1.5 rounded-lg border border-noite/20 text-cinza-texto hover:bg-lavanda transition-colors"
          >
            Ver área do aluno
          </Link>
        </div>
      </div>

      {/* KPIs */}
      {analytics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <KpiCard
            label="Alunos únicos"
            value={analytics.total_alunos}
          />
          <KpiCard
            label="Aproveitamento médio"
            value={analytics.aproveitamento_medio != null ? `${analytics.aproveitamento_medio}%` : null}
            sub={aproveitamentoPorModo}
          />
          <KpiCard
            label="Total de submissões"
            value={analytics.total_submissoes}
          />
          <KpiCard
            label="Atividades"
            value={turma.exams.length}
            sub={contagemPorModo(turma.exams)}
          />
        </div>
      )}

      <FunilDaTurma turmaId={turmaId} recarga={recargaFunil} />

      {/* Charts — só mostra se há dados */}
      {analytics && (evolucaoData.length > 0 || errosData.length > 0) && (
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Evolução entre provas */}
          {evolucaoData.length > 0 && (
            <div className="bg-white rounded-xl border border-noite/20 p-5">
              <h2 className="text-sm font-semibold text-cinza-texto mb-4">Taxa de aprovação por atividade</h2>
              <BarList
                max={100}
                items={evolucaoData.map(d => ({
                  label: truncar(d.name), title: d.name,
                  value: d.taxa, display: `${d.taxa}%`, color: rateColor(d.taxa),
                }))}
              />
            </div>
          )}

          {/* Top erros */}
          {errosData.length > 0 && (
            <div className="bg-white rounded-xl border border-noite/20 p-5">
              <h2 className="text-sm font-semibold text-cinza-texto mb-4">Erros mais frequentes</h2>
              <BarList
                color={ERR_COLOR}
                items={errosData.map(e => ({ label: e.name, title: e.full, value: e.count }))}
              />
            </div>
          )}
        </div>
      )}

      {analytics?.trajetoria?.length > 0 && (
        <TrajetoriaDeErros trajetoria={analytics.trajetoria} />
      )}

      {/* Atividades: provas e listas são o mesmo tipo de atividade, separadas pelo modo */}
      <div>
        <h2 className="text-sm font-semibold text-cinza-texto uppercase tracking-wide mb-3">Atividades</h2>
        {turma.exams.length === 0 ? (
          <div className="text-center py-16 text-cinza-texto">
            <svg className="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
            </svg>
            <p className="text-sm">Nenhuma atividade cadastrada.</p>
            <p className="text-xs mt-1">Clique em "Nova atividade" para adicionar uma prova ou uma lista.</p>
          </div>
        ) : (
          <>
            <ListControls
              search={search} onSearch={setSearch}
              sort={sort} onSort={setSort}
              sortOptions={SORT_OPTIONS}
              placeholder="Buscar prova ou lista pelo nome…"
            />
            {GRUPOS_DE_ATIVIDADE.map(({ modo, titulo, vazio }) => {
              const doGrupo = displayedExams.filter(exam => (exam.modo || 'prova') === modo)
              return (
                <div key={modo} className="mt-5 first:mt-0">
                  <h3 className="text-xs font-semibold text-cinza-texto uppercase tracking-wide mb-2">
                    {titulo} ({doGrupo.length})
                  </h3>
                  {doGrupo.length === 0 ? (
                    <p className="text-sm text-cinza-texto py-4">
                      {search.trim() ? 'Nada encontrado para o filtro.' : vazio}
                    </p>
                  ) : (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {doGrupo.map(exam => {
              const ea = examAnalyticsMap[exam.id]
              return (
                <div
                  key={exam.id}
                  className="bg-white rounded-xl border border-noite/20 p-5 hover:border-violeta/50 hover:shadow-sm transition-all flex flex-col"
                >
                  <div onClick={() => navigate(`/exam/${exam.id}`)} className="cursor-pointer flex-1">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h2 className="text-sm font-semibold text-noite leading-tight truncate flex-1">
                        {exam.titulo || exam.filename}
                      </h2>
                      <Badge color={exam.modo === 'treino' ? 'purple' : 'gray'}>{modoLabel(exam.modo)}</Badge>
                      {!exam.publicada && <Badge color="yellow">rascunho</Badge>}
                    </div>
                    <div className="flex gap-4 text-xs text-cinza-texto mb-1">
                      <span>{exam.question_count} {exam.question_count === 1 ? 'questão' : 'questões'}</span>
                      <span>{exam.submission_count} {exam.submission_count === 1 ? 'submissão' : 'submissões'}</span>
                      {ea && <span>{ea.total_alunos} {ea.total_alunos === 1 ? 'aluno' : 'alunos'}</span>}
                    </div>
                    {ea && <PassRateBar rate={ea.pass_rate} />}
                    <p className="text-xs text-cinza-texto mt-2">{formatDate(exam.created_at)}</p>
                  </div>
                  <div className="flex justify-end mt-3 pt-3 border-t border-noite/10">
                    <button
                      onClick={() => setDeleteExamTarget(exam)}
                      className="text-xs px-2.5 py-1.5 rounded-md border border-erro/30 text-erro hover:bg-erro-fundo transition-colors"
                    >
                      Excluir
                    </button>
                  </div>
                </div>
              )
                      })}
                    </div>
                  )}
                </div>
              )
            })}
          </>
        )}
      </div>

      <ConfirmDialog
        open={!!deleteExamTarget}
        onClose={() => setDeleteExamTarget(null)}
        onConfirm={confirmDeleteExam}
        loading={deletingExam}
        title="Excluir atividade"
        confirmLabel="Excluir atividade"
        message={deleteExamTarget
          ? `Excluir "${deleteExamTarget.titulo || deleteExamTarget.filename}"? Todas as questões, test cases e submissões serão removidos permanentemente.`
          : ''}
      />
    </div>
  )
}
