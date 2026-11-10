import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { listarAtividades, listarMinhasTurmas } from '../../api/aluno'
import AtividadeCard from '../../components/AtividadeCard'
import Spinner from '../../components/Spinner'
import Card from '../../components/ui/Card'
import RotuloSecao from '../../components/ui/RotuloSecao'
import { ordenarAtividades } from '../../utils/atividade'

// Modo diz o que a atividade é, e é a primeira pergunta do aluno ao abrir a turma.
const GRUPOS = [
  { modo: 'prova', titulo: 'Provas', vazio: 'Nenhuma prova nesta turma.' },
  { modo: 'treino', titulo: 'Listas', vazio: 'Nenhuma lista nesta turma.' },
]

function Grupo({ titulo, vazio, atividades }) {
  return (
    <section className="space-y-3">
      <RotuloSecao as="h2">{titulo}</RotuloSecao>
      {atividades.length === 0 ? (
        <p className="text-sm text-cinza-texto">{vazio}</p>
      ) : (
        <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
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
        <Spinner className="w-6 h-6 text-violeta" />
      </div>
    )
  }

  if (!turma) {
    return (
      <div className="space-y-3">
        <Link to="/aluno/turmas" className="inline-flex items-center gap-1 min-h-11 text-sm font-bold text-cinza-texto hover:text-noite">
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Turmas
        </Link>
        <p className="text-sm text-erro">{erro}</p>
      </div>
    )
  }

  const ordenadas = ordenarAtividades(atividades)

  return (
    <div className="space-y-8">
      <div>
        <Link to="/aluno/turmas" className="inline-flex items-center gap-1 min-h-11 text-sm font-bold text-cinza-texto hover:text-noite">
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Turmas
        </Link>
        <h1 className="mt-1 titulo-pagina break-words">{turma.nome}</h1>
        <p className="mt-1 text-xs text-cinza-texto">
          {turma.professor_nome || 'sem professor'}
          {turma.codigo && <span className="font-mono"> · {turma.codigo}</span>}
        </p>
      </div>

      {atividades.length === 0 ? (
        <Card className="border-dashed border-noite/30! text-center p-10!">
          <p className="text-sm text-cinza-texto">Nenhuma atividade ainda.</p>
          <p className="text-xs text-cinza-texto">
            O professor ainda não publicou nada nesta turma.
          </p>
        </Card>
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
