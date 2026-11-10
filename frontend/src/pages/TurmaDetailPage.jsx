import { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams, Link } from 'react-router-dom'
import { ChevronRight, ClipboardList, Plus, Trash2, Upload } from 'lucide-react'
import { adicionarListaDeAquecimento, getTurma, getTurmaAnalytics, deleteExam } from '../api/exam'
import Spinner from '../components/Spinner'
import ConfirmDialog from '../components/ConfirmDialog'
import ListControls from '../components/ListControls'
import Badge from '../components/Badge'
import BarList from '../components/BarList'
import TrajetoriaDeErros from '../components/TrajetoriaDeErros'
import FunilDaTurma from '../components/FunilDaTurma'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import PainelDestaque from '../components/ui/PainelDestaque'
import Progresso from '../components/ui/Progresso'
import RotuloSecao from '../components/ui/RotuloSecao'
import Tag from '../components/ui/Tag'
import { COR_ERRO, corDaTaxa } from '../utils/coresGraficos'
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

function KpiCard({ label, value, sub }) {
  return (
    <Card className="gap-1!">
      <RotuloSecao>{label}</RotuloSecao>
      <p className="font-titulo font-extrabold text-3xl text-noite">{value ?? '—'}</p>
      {sub && <p className="text-sm text-cinza-texto">{sub}</p>}
    </Card>
  )
}

function PassRateBar({ rate }) {
  if (rate == null) return <span className="text-sm text-cinza-texto">sem dados</span>
  return (
    <div className="flex items-center gap-2 mt-2">
      <div className="flex-1">
        <Progresso valor={rate} rotulo="Taxa de aprovação" cor={corDaTaxa(rate)} />
      </div>
      <span className="text-[13px] font-bold text-noite w-10 text-right">{rate}%</span>
    </div>
  )
}

export default function TurmaDetailPage() {
  const { turmaId } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const secaoPedida = searchParams.get('secao')
  const secao = ['panorama', 'atividades', 'desempenho'].includes(secaoPedida) ? secaoPedida : 'panorama'
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
      `Nossa turma de ${turma.nome} vai usar o CentralizEd nas listas e no treino. ` +
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
      <div className="flex items-center gap-1 text-sm text-cinza-texto lg:hidden">
        <Link to="/" className="hover:text-noite">Turmas</Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
      </div>

      <PainelDestaque>
        <div className="space-y-5 pr-0 sm:pr-24">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="titulo-pagina break-words">{turma.nome}</h1>
            <Tag>{turma.codigo}</Tag>
          </div>
          <div>
            <p className="font-titulo font-extrabold text-[13px] uppercase tracking-[0.1em] text-white/80">
              Código de acesso da turma
            </p>
            <p className="mt-1 font-titulo font-extrabold text-2xl">
              {turma.codigo_acesso || '—'}
            </p>
            <p className="text-sm text-white/80 mt-1">
              Passe o código ou o convite com link, que já leva o código. {turma.aluno_count ?? 0} já {(turma.aluno_count ?? 0) === 1 ? 'entrou' : 'entraram'} com conta.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Botao variante="secundario" onClick={copiarCodigo} disabled={!turma.codigo_acesso}>
              {copiado ? 'Copiado' : 'Copiar código'}
            </Botao>
            <Botao variante="secundario" onClick={copiarConvite} disabled={!turma.codigo_acesso}>
              {conviteCopiado ? 'Copiado' : 'Copiar convite'}
            </Botao>
            <Botao variante="secundario" to="/aluno/login" target="_blank">
              Ver área do aluno
            </Botao>
            {!turma.exams.some(e => e.filename === 'lista-de-aquecimento') && (
              <Botao variante="secundario" onClick={adicionarAquecimento} disabled={adicionandoAquecimento}>
                <Plus className="w-4 h-4" aria-hidden="true" />
                {adicionandoAquecimento ? 'Adicionando...' : 'Adicionar lista de aquecimento'}
              </Botao>
            )}
            <Botao variante="secundario" onClick={() => navigate(`/turma/${turmaId}/upload`)}>
              <Upload className="w-4 h-4" aria-hidden="true" />
              Nova atividade
            </Botao>
          </div>
          {erroAquecimento && <p className="text-sm text-white font-bold">{erroAquecimento}</p>}
        </div>
      </PainelDestaque>

      <div hidden={secao !== 'panorama'}>
        <FunilDaTurma turmaId={turmaId} recarga={recargaFunil} />
      </div>

      <div hidden={secao !== 'desempenho'} className="space-y-6">
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

        {analytics && (evolucaoData.length > 0 || errosData.length > 0) && (
          <div className="grid gap-6 lg:grid-cols-2">
            {evolucaoData.length > 0 && (
              <Card principal>
                <h2 className="titulo-card">Taxa de aprovação por atividade</h2>
                <BarList
                  max={100}
                  items={evolucaoData.map(d => ({
                    label: truncar(d.name), title: d.name,
                    value: d.taxa, display: `${d.taxa}%`, color: corDaTaxa(d.taxa),
                  }))}
                />
              </Card>
            )}

            {errosData.length > 0 && (
              <Card principal>
                <h2 className="titulo-card">Erros mais frequentes</h2>
                <BarList
                  color={COR_ERRO}
                  items={errosData.map(e => ({ label: e.name, title: e.full, value: e.count }))}
                />
              </Card>
            )}
          </div>
        )}

        {analytics?.trajetoria?.length > 0 && (
          <TrajetoriaDeErros trajetoria={analytics.trajetoria} />
        )}
      </div>

      {/* Atividades: provas e listas são o mesmo tipo de atividade, separadas pelo modo */}
      <div hidden={secao !== 'atividades'} className="space-y-4">
        <RotuloSecao as="h2">Atividades</RotuloSecao>
        {turma.exams.length === 0 ? (
          <Card className="border-dashed border-noite/30! text-center p-10! items-center">
            <ClipboardList className="w-10 h-10 text-violeta" aria-hidden="true" />
            <p className="font-bold">Nenhuma atividade cadastrada.</p>
            <p className="text-sm text-cinza-texto">Clique em "Nova atividade" para adicionar uma prova ou uma lista.</p>
          </Card>
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
                  <RotuloSecao as="h3" className="mb-3">
                    {titulo} ({doGrupo.length})
                  </RotuloSecao>
                  {doGrupo.length === 0 ? (
                    <p className="text-sm text-cinza-texto py-2">
                      {search.trim() ? 'Nada encontrado para o filtro.' : vazio}
                    </p>
                  ) : (
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {doGrupo.map(exam => {
              const ea = examAnalyticsMap[exam.id]
              return (
                <Card key={exam.id} principal>
                  <div onClick={() => navigate(`/exam/${exam.id}`)} className="cursor-pointer flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h2 className="titulo-card leading-tight min-w-0 break-words flex-1">
                        {exam.titulo || exam.filename}
                      </h2>
                      <div className="flex flex-wrap justify-end gap-1 shrink-0">
                        <Badge color={exam.modo === 'treino' ? 'purple' : 'gray'}>{modoLabel(exam.modo)}</Badge>
                        {!exam.publicada && <Badge color="yellow">rascunho</Badge>}
                      </div>
                    </div>
                    <div className="flex flex-wrap gap-x-4 text-sm text-cinza-texto mb-1">
                      <span>{exam.question_count} {exam.question_count === 1 ? 'questão' : 'questões'}</span>
                      <span>{exam.submission_count} {exam.submission_count === 1 ? 'submissão' : 'submissões'}</span>
                      {ea && <span>{ea.total_alunos} {ea.total_alunos === 1 ? 'aluno' : 'alunos'}</span>}
                    </div>
                    {ea && <PassRateBar rate={ea.pass_rate} />}
                    <p className="text-[13px] text-cinza-texto mt-2">{formatDate(exam.created_at)}</p>
                  </div>
                  <div className="flex justify-end pt-3 border-t-2 border-noite/10">
                    <Botao variante="perigo" onClick={() => setDeleteExamTarget(exam)} className="min-h-9! px-3.5! text-[13px]!">
                      <Trash2 className="w-4 h-4" aria-hidden="true" />
                      Excluir
                    </Botao>
                  </div>
                </Card>
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
