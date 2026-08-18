import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { entrarNaTurma, listarAtividades, listarMinhasTurmas } from '../../api/aluno'
import Badge from '../../components/Badge'
import Spinner from '../../components/Spinner'
import { janelaTexto, modoLabel, situacaoInfo } from '../../utils/atividade'

function ProgressoBarra({ resolvidas, total }) {
  const pct = total > 0 ? Math.round((resolvidas / total) * 100) : 0
  return (
    <div className="flex items-center gap-2 mt-3">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full rounded-full bg-purple-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-24 text-right">{resolvidas}/{total} questões</span>
    </div>
  )
}

function AtividadeCard({ atividade }) {
  const situacao = situacaoInfo(atividade.situacao)
  const janela = janelaTexto(atividade)
  const concluida = atividade.total_questoes > 0
    && atividade.questoes_resolvidas === atividade.total_questoes

  return (
    <Link
      to={`/aluno/atividades/${atividade.exam_id}`}
      className="block bg-white rounded-xl border border-gray-200 p-5 hover:border-purple-300 transition-colors"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{atividade.titulo}</p>
          <p className="text-xs text-gray-400 mt-0.5">{atividade.turma_nome}</p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge color={atividade.modo === 'treino' ? 'purple' : 'gray'}>
            {modoLabel(atividade.modo)}
          </Badge>
          {concluida
            ? <Badge color="green">Concluída</Badge>
            : <Badge color={situacao.color}>{situacao.label}</Badge>}
        </div>
      </div>

      <ProgressoBarra resolvidas={atividade.questoes_resolvidas} total={atividade.total_questoes} />

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
        <span>{atividade.tentativas} tentativa{atividade.tentativas === 1 ? '' : 's'}</span>
        {atividade.max_tentativas != null && (
          <span>máx. {atividade.max_tentativas} por questão</span>
        )}
        {janela && <span>{janela}</span>}
      </div>
    </Link>
  )
}

export default function AlunoHomePage() {
  const [turmas, setTurmas] = useState([])
  const [atividades, setAtividades] = useState([])
  const [loading, setLoading] = useState(true)
  const [codigo, setCodigo] = useState('')
  const [entrando, setEntrando] = useState(false)
  const [erroCodigo, setErroCodigo] = useState('')
  const [sucesso, setSucesso] = useState('')

  const carregar = () => Promise.all([listarMinhasTurmas(), listarAtividades()])
    .then(([t, a]) => { setTurmas(t.data); setAtividades(a.data) })
    .finally(() => setLoading(false))

  useEffect(() => { carregar() }, [])

  const handleEntrar = async (e) => {
    e.preventDefault()
    if (!codigo.trim()) return
    setErroCodigo('')
    setSucesso('')
    setEntrando(true)
    try {
      const { data } = await entrarNaTurma(codigo.trim())
      setSucesso(`Você entrou em ${data.nome}.`)
      setCodigo('')
      await carregar()
    } catch (err) {
      setErroCodigo(err.response?.data?.detail || 'Não foi possível entrar na turma.')
    } finally {
      setEntrando(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-semibold text-gray-900 mb-1">Entrar em uma turma</h2>
        <p className="text-xs text-gray-400 mb-4">Use o código de 6 caracteres que o professor passou.</p>
        <form onSubmit={handleEntrar} className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            value={codigo}
            onChange={e => setCodigo(e.target.value.toUpperCase())}
            placeholder="ABC234"
            maxLength={6}
            className="flex-1 text-sm font-mono tracking-widest uppercase rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={entrando || !codigo.trim()}
            className="inline-flex items-center justify-center gap-2 text-sm px-5 py-2.5 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {entrando && <Spinner className="w-4 h-4" />}
            Entrar
          </button>
        </form>
        {erroCodigo && <p className="mt-2 text-xs text-red-600">{erroCodigo}</p>}
        {sucesso && <p className="mt-2 text-xs text-green-600">{sucesso}</p>}
      </div>

      {turmas.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-900 mb-3">Minhas turmas</h2>
          <div className="flex flex-wrap gap-2">
            {turmas.map(t => (
              <div key={t.id} className="bg-white rounded-lg border border-gray-200 px-4 py-2.5">
                <p className="text-sm text-gray-900">{t.nome}</p>
                <p className="text-xs text-gray-400">
                  {t.professor_nome || 'sem professor'} · {t.exam_count} atividade{t.exam_count === 1 ? '' : 's'}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="text-sm font-semibold text-gray-900 mb-3">Atividades</h2>
        {atividades.length === 0 ? (
          <div className="bg-white rounded-xl border border-dashed border-gray-200 p-10 text-center">
            <p className="text-sm text-gray-500">Nenhuma atividade ainda.</p>
            <p className="text-xs text-gray-400 mt-1">
              Entre em uma turma com o código do professor para ver as atividades dela.
            </p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {atividades.map(a => <AtividadeCard key={a.exam_id} atividade={a} />)}
          </div>
        )}
      </div>
    </div>
  )
}
