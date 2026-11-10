import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listarMinhasTurmas } from '../../api/aluno'
import EntrarNaTurma from '../../components/EntrarNaTurma'
import Spinner from '../../components/Spinner'
import Card from '../../components/ui/Card'

function TurmaCard({ turma }) {
  return (
    <Card
      as={Link}
      to={`/aluno/turmas/${turma.id}`}
      principal
      className="gap-2! transition-transform active:translate-x-0.5 active:translate-y-0.5"
    >
      <p className="titulo-card break-words">{turma.nome}</p>
      <p className="text-xs text-cinza-texto">{turma.professor_nome || 'sem professor'}</p>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-cinza-texto">
        <span>{turma.exam_count} atividade{turma.exam_count === 1 ? '' : 's'}</span>
        {turma.codigo && <span className="font-mono">{turma.codigo}</span>}
      </div>
    </Card>
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
        <Spinner className="w-6 h-6 text-violeta" />
      </div>
    )
  }

  // Conta nova cai aqui: uma tela só, com o que ela precisa fazer.
  if (turmas.length === 0) {
    return (
      <div className="max-w-md mx-auto py-10 space-y-4">
        <div className="text-center">
          <h1 className="titulo-pagina">Comece entrando na sua turma</h1>
          <p className="mt-1 text-sm text-cinza-texto">
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
        <h1 className="titulo-pagina">Minhas turmas</h1>
        <p className="mt-1 text-sm text-cinza-texto">Escolha uma turma para ver as atividades dela.</p>
      </div>

      <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
        {turmas.map(t => <TurmaCard key={t.id} turma={t} />)}
      </div>

      <EntrarNaTurma aoEntrar={carregar} />
    </div>
  )
}
