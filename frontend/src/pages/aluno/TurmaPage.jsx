import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { listarAtividades, listarMinhasTurmas } from '../../api/aluno'
import AtividadeCard from '../../components/AtividadeCard'
import Spinner from '../../components/Spinner'
import { ordenarAtividades } from '../../utils/atividade'

// Modo diz o que a atividade é, e é a primeira pergunta do aluno ao abrir a turma.
const GRUPOS = [
  { modo: 'prova', titulo: 'Provas', vazio: 'Nenhuma prova nesta turma.' },
  { modo: 'treino', titulo: 'Treinos', vazio: 'Nenhum treino nesta turma.' },
]

function Grupo({ titulo, vazio, atividades }) {
  return (
    <section>
      <h2 className="text-sm font-semibold text-gray-900 mb-3">{titulo}</h2>
      {atividades.length === 0 ? (
        <p className="text-sm text-gray-400">{vazio}</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {atividades.map(a => <AtividadeCard key={a.exam_id} atividade={a} />)}
        </div>
      )}
    </section>
  )
}

export default function TurmaPage() {
  const { turmaId } = useParams()
  const [turma, setTurma] = useState(null)
  const [atividades, setAtividades] = useState([])
  const [loading, setLoading] = useState(true)
  const [erro, setErro] = useState('')

  useEffect(() => {
    // Trocar de turma dispara nova busca: descarta a resposta que chegar atrasada.
    let ativo = true
    // A turma sai da lista de matrículas: o aluno só enxerga as suas.
    Promise.all([listarMinhasTurmas(), listarAtividades(turmaId)])
      .then(([t, a]) => {
        if (!ativo) return
        const minha = t.data.find(x => String(x.id) === String(turmaId))
        if (!minha) {
          setTurma(null)
          setErro('Turma não encontrada entre as suas.')
          return
        }
        setErro('')
        setTurma(minha)
        setAtividades(a.data)
      })
      .catch(err => {
        if (ativo) setErro(err.response?.data?.detail || 'Não foi possível carregar a turma.')
      })
      .finally(() => { if (ativo) setLoading(false) })
    return () => { ativo = false }
  }, [turmaId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  if (!turma) {
    return (
      <div className="space-y-3">
        <Link to="/aluno/turmas" className="text-xs text-gray-400 hover:text-gray-600">← Turmas</Link>
        <p className="text-sm text-red-600">{erro}</p>
      </div>
    )
  }

  const ordenadas = ordenarAtividades(atividades)

  return (
    <div className="space-y-8">
      <div>
        <Link to="/aluno/turmas" className="text-xs text-gray-400 hover:text-gray-600">← Turmas</Link>
        <h1 className="mt-2 text-xl font-semibold text-gray-900">{turma.nome}</h1>
        <p className="mt-1 text-xs text-gray-400">
          {turma.professor_nome || 'sem professor'}
          {turma.codigo && <span className="font-mono"> · {turma.codigo}</span>}
        </p>
      </div>

      {atividades.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-200 p-10 text-center">
          <p className="text-sm text-gray-500">Nenhuma atividade ainda.</p>
          <p className="text-xs text-gray-400 mt-1">
            O professor ainda não publicou nada nesta turma.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {GRUPOS.map(({ modo, titulo, vazio }) => (
            <Grupo
              key={modo}
              titulo={titulo}
              vazio={vazio}
              atividades={ordenadas.filter(a => a.modo === modo)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
