import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { entrarNaTurma } from '../../api/aluno'
import { useAlunoAuth } from '../../context/AlunoAuthContext'
import { apagarConvite, guardarConvite } from '../../utils/convitePendente'
import TelaDeEntrada from '../../components/TelaDeEntrada'
import Botao from '../../components/ui/Botao'
import Card from '../../components/ui/Card'
import Spinner from '../../components/Spinner'

export default function ConvitePage() {
  const { codigo } = useParams()
  const { isAuthenticated, loading } = useAlunoAuth()
  const navigate = useNavigate()
  const [situacao, setSituacao] = useState('entrando')
  const [tentativa, setTentativa] = useState(0)

  // Guarda antes de tudo: com o token vencido, o cliente do aluno manda direto
  // para o login, e o código precisa sobreviver até a volta.
  useEffect(() => {
    guardarConvite(codigo)
  }, [codigo])

  useEffect(() => {
    if (loading) return
    if (!isAuthenticated) {
      navigate('/aluno/cadastro', { replace: true })
      return
    }
    let ativo = true
    entrarNaTurma(codigo, 'convite')
      .then(({ data }) => {
        if (!ativo) return
        apagarConvite()
        navigate(`/aluno/turmas/${data.id}?via=convite`, { replace: true })
      })
      .catch((err) => {
        if (!ativo) return
        if (err.response?.status === 404) {
          apagarConvite()
          setSituacao('invalido')
        } else {
          setSituacao('falhou')
        }
      })
    return () => { ativo = false }
  }, [codigo, isAuthenticated, loading, navigate, tentativa])

  const tentarDeNovo = () => {
    setSituacao('entrando')
    setTentativa(t => t + 1)
  }

  return (
    <TelaDeEntrada frase="Entenda o seu erro e tente de novo.">
      <Card principal className="text-center">
        {situacao === 'entrando' && (
          <div className="flex flex-col items-center gap-3">
            <Spinner className="w-6 h-6 text-violeta" />
            <p className="text-sm text-cinza-texto">Entrando na turma...</p>
          </div>
        )}
        {situacao === 'invalido' && (
          <>
            <p className="text-sm text-cinza-texto mb-4">
              Este convite não vale mais. Peça o código ao professor.
            </p>
            <Link to="/aluno/turmas" className="text-sm text-violeta hover:underline font-medium">
              Ir para minhas turmas
            </Link>
          </>
        )}
        {situacao === 'falhou' && (
          <>
            <p className="text-sm text-cinza-texto mb-4">Não foi possível entrar na turma agora.</p>
            <Botao onClick={tentarDeNovo}>Tentar de novo</Botao>
          </>
        )}
      </Card>
    </TelaDeEntrada>
  )
}
