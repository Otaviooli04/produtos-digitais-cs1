import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { entrarNaTurma, listarMinhasTurmas } from '../../api/aluno'
import Spinner from '../../components/Spinner'

function EntrarNaTurma({ aoEntrar }) {
  const [codigo, setCodigo] = useState('')
  const [entrando, setEntrando] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!codigo.trim()) return
    setErro('')
    setSucesso('')
    setEntrando(true)
    try {
      const { data } = await entrarNaTurma(codigo.trim())
      setSucesso(`Você entrou em ${data.nome}.`)
      setCodigo('')
      await aoEntrar()
    } catch (err) {
      setErro(err.response?.data?.detail || 'Não foi possível entrar na turma.')
    } finally {
      setEntrando(false)
    }
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-sm font-semibold text-gray-900 mb-1">Entrar em uma turma</h2>
      <p className="text-xs text-gray-400 mb-4">Use o código de 6 caracteres que o professor passou.</p>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
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
      {erro && <p className="mt-2 text-xs text-red-600">{erro}</p>}
      {sucesso && <p className="mt-2 text-xs text-green-600">{sucesso}</p>}
    </div>
  )
}

function TurmaCard({ turma }) {
  return (
    <Link
      to={`/aluno/turmas/${turma.id}`}
      className="block bg-white rounded-xl border border-gray-200 p-5 hover:border-purple-300 transition-colors"
    >
      <p className="text-sm font-medium text-gray-900 truncate">{turma.nome}</p>
      <p className="text-xs text-gray-400 mt-0.5">{turma.professor_nome || 'sem professor'}</p>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
        <span>{turma.exam_count} atividade{turma.exam_count === 1 ? '' : 's'}</span>
        {turma.codigo && <span className="font-mono">{turma.codigo}</span>}
      </div>
    </Link>
  )
}

export default function TurmasPage() {
  const [turmas, setTurmas] = useState([])
  const [loading, setLoading] = useState(true)

  const carregar = () => listarMinhasTurmas()
    .then(({ data }) => setTurmas(data))
    .finally(() => setLoading(false))

  useEffect(() => { carregar() }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  // Conta nova cai aqui: uma tela só, com o que ela precisa fazer.
  if (turmas.length === 0) {
    return (
      <div className="max-w-md mx-auto py-10 space-y-4">
        <div className="text-center">
          <h1 className="text-xl font-semibold text-gray-900">Comece entrando na sua turma</h1>
          <p className="mt-1 text-sm text-gray-500">
            Suas atividades aparecem aqui assim que você entrar.
          </p>
        </div>
        <EntrarNaTurma aoEntrar={carregar} />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Minhas turmas</h1>
        <p className="mt-1 text-sm text-gray-500">Escolha uma turma para ver as atividades dela.</p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {turmas.map(t => <TurmaCard key={t.id} turma={t} />)}
      </div>

      <EntrarNaTurma aoEntrar={carregar} />
    </div>
  )
}
