import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { gerarExercicio, getTrilha } from '../../api/aluno'
import Badge from '../../components/Badge'
import Spinner from '../../components/Spinner'
import { shortError } from '../../utils/errorLabels'

/**
 * A trilha de treino. O painel de progresso já dizia ao aluno o que ele repete;
 * aqui ele treina exatamente isso, com exercício gerado sob medida e tentativas
 * ilimitadas. Nada daqui vale nota.
 */
export default function TreinoPage() {
  const [trilha, setTrilha] = useState(null)
  const [loading, setLoading] = useState(true)
  const [gerando, setGerando] = useState(null)
  const [erro, setErro] = useState('')

  const carregar = () => getTrilha().then(({ data }) => setTrilha(data))

  useEffect(() => {
    carregar().finally(() => setLoading(false))
  }, [])

  const gerar = async (categoria) => {
    setErro('')
    setGerando(categoria || 'auto')
    try {
      const { data } = await gerarExercicio(categoria)
      await carregar()
      window.location.assign(`/aluno/treino/${data.id}`)
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível gerar agora.')
    } finally {
      setGerando(null)
    }
  }

  if (loading) {
    return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  }

  const categorias = trilha?.categorias ?? []
  const exercicios = trilha?.exercicios ?? []
  const pendentes = exercicios.filter(e => !e.resolvido)
  const resolvidos = exercicios.filter(e => e.resolvido)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Treino</h1>
        <p className="text-sm text-gray-500 mt-0.5">
          Exercícios feitos para o erro que você mais repete. Tentativas ilimitadas,
          e nada daqui entra na sua nota.
        </p>
      </div>

      {erro && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {erro}
        </div>
      )}

      {categorias.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-sm">A trilha começa a partir dos seus erros.</p>
          <p className="text-xs mt-1">
            Resolva alguma questão da sua turma e volte aqui.
          </p>
          <Link to="/aluno/turmas" className="inline-block mt-4 text-sm text-purple-600 hover:text-purple-700">
            Ver minhas turmas
          </Link>
        </div>
      ) : (
        <>
          {pendentes.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Para resolver
              </h2>
              <div className="space-y-2">
                {pendentes.map(e => <CartaoExercicio key={e.id} exercicio={e} />)}
              </div>
            </div>
          )}

          <div>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              O que você mais erra
            </h2>
            <div className="space-y-2">
              {categorias.map(c => (
                <div key={c.error_category} className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge color="red">{shortError(c.error_category)}</Badge>
                    <span className="text-xs text-gray-400">
                      {c.ocorrencias}× nas suas tentativas
                    </span>
                    {c.exercicios_resolvidos > 0 && (
                      <span className="text-xs text-green-600">
                        · {c.exercicios_resolvidos} treino{c.exercicios_resolvidos !== 1 ? 's' : ''} resolvido{c.exercicios_resolvidos !== 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                  {c.o_que_fazer && (
                    <p className="text-sm text-gray-600 mt-2">{c.o_que_fazer}</p>
                  )}
                  <button
                    onClick={() => gerar(c.error_category)}
                    disabled={gerando != null}
                    className="mt-3 inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors"
                  >
                    {gerando === c.error_category && <Spinner className="w-3.5 h-3.5" />}
                    {c.tem_pendente ? 'Continuar treinando' : 'Treinar isso'}
                  </button>
                </div>
              ))}
            </div>
          </div>

          {resolvidos.length > 0 && (
            <div>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Já resolvidos
              </h2>
              <div className="space-y-2">
                {resolvidos.map(e => <CartaoExercicio key={e.id} exercicio={e} />)}
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400">
            {trilha.geracoes_restantes_hoje > 0
              ? `Você pode gerar mais ${trilha.geracoes_restantes_hoje} exercício${trilha.geracoes_restantes_hoje !== 1 ? 's' : ''} hoje. Treinar nos que já estão aqui é ilimitado.`
              : 'Você atingiu o limite de exercícios novos por hoje. Treinar nos que já estão aqui continua liberado.'}
          </p>
        </>
      )}
    </div>
  )
}

function CartaoExercicio({ exercicio }) {
  return (
    <Link
      to={`/aluno/treino/${exercicio.id}`}
      className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-purple-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-medium text-gray-900">{exercicio.titulo}</span>
        {exercicio.resolvido && <Badge color="green">resolvido</Badge>}
        <span className="ml-auto text-xs text-gray-400">
          {exercicio.tentativas} tentativa{exercicio.tentativas !== 1 ? 's' : ''}
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-1">{shortError(exercicio.error_category)}</p>
    </Link>
  )
}
