import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { gerarExercicio, getTrilha } from '../../api/aluno'
import Badge from '../../components/Badge'
import Spinner from '../../components/Spinner'
import Botao from '../../components/ui/Botao'
import Card from '../../components/ui/Card'
import RotuloSecao from '../../components/ui/RotuloSecao'
import Tag from '../../components/ui/Tag'
import { dataCurta } from '../../utils/datas'
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
    return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>
  }

  const categorias = trilha?.categorias ?? []
  const superados = trilha?.superados ?? []
  const exercicios = trilha?.exercicios ?? []
  const pendentes = exercicios.filter(e => !e.resolvido)
  const resolvidos = exercicios.filter(e => e.resolvido)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="titulo-pagina">Treino</h1>
        <p className="text-sm text-cinza-texto mt-0.5">
          Exercícios feitos para o erro que você mais repete. Tentativas ilimitadas,
          e nada daqui entra na sua nota.
        </p>
      </div>

      {erro && (
        <div className="rounded-botao border-2 border-aviso bg-aviso-fundo px-4 py-3 text-sm text-aviso">
          {erro}
        </div>
      )}

      {categorias.length === 0 && superados.length === 0 ? (
        <div className="text-center py-16 text-cinza-texto">
          <p className="text-sm">A trilha começa a partir dos seus erros.</p>
          <p className="text-xs mt-1">
            Resolva alguma questão da sua turma e volte aqui.
          </p>
          <Botao to="/aluno/turmas" className="mt-4">
            Ver minhas turmas
          </Botao>
        </div>
      ) : (
        <>
          {pendentes.length > 0 && (
            <div className="space-y-3">
              <RotuloSecao as="h2">
                Para resolver
              </RotuloSecao>
              <div className="space-y-2">
                {pendentes.map(e => <CartaoExercicio key={e.id} exercicio={e} />)}
              </div>
            </div>
          )}

          {categorias.length > 0 ? (
            <div className="space-y-3">
              <RotuloSecao as="h2">
                O que você mais erra
              </RotuloSecao>
              <div className="space-y-2">
                {categorias.map(c => (
                  <Card key={c.error_category} className="gap-2!">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge color="red">{shortError(c.error_category)}</Badge>
                      <span className="text-xs text-cinza-texto">
                        {c.ocorrencias}× nas suas tentativas
                      </span>
                      {c.exercicios_resolvidos > 0 && (
                        <span className="text-xs text-sucesso">
                          · {c.exercicios_resolvidos} treino{c.exercicios_resolvidos !== 1 ? 's' : ''} resolvido{c.exercicios_resolvidos !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    {c.o_que_fazer && (
                      <p className="text-sm text-cinza-texto">{c.o_que_fazer}</p>
                    )}
                    <div>
                      <Botao onClick={() => gerar(c.error_category)} disabled={gerando != null}>
                        {gerando === c.error_category && <Spinner className="w-3.5 h-3.5" />}
                        {c.tem_pendente ? 'Continuar treinando' : 'Treinar isso'}
                      </Botao>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ) : (
            <Card className="border-dashed border-noite/30! text-center p-8! items-center">
              <p className="text-sm text-cinza-texto">Você superou todos os erros que repetia.</p>
              <p className="text-xs text-cinza-texto">Resolva uma questão da sua turma e volte aqui.</p>
              <Botao to="/aluno/turmas" className="mt-1">
                Ver minhas turmas
              </Botao>
            </Card>
          )}

          {superados.length > 0 && (
            <div className="space-y-3">
              <RotuloSecao as="h2">
                Erros que você superou
              </RotuloSecao>
              <div className="space-y-2">
                {superados.map(s => (
                  <Card key={s.error_category} className="gap-2!">
                    <div className="flex flex-wrap items-center gap-2">
                      <Tag variante="sucesso">{shortError(s.error_category)}</Tag>
                      <span className="text-xs text-cinza-texto">superado em {dataCurta(s.superado_em)}</span>
                    </div>
                    <div>
                      <Botao variante="secundario" onClick={() => gerar(s.error_category)} disabled={gerando != null}>
                        {gerando === s.error_category && <Spinner className="w-3.5 h-3.5" />}
                        Treinar de novo
                      </Botao>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {resolvidos.length > 0 && (
            <div className="space-y-3">
              <RotuloSecao as="h2">
                Já resolvidos
              </RotuloSecao>
              <div className="space-y-2">
                {resolvidos.map(e => <CartaoExercicio key={e.id} exercicio={e} />)}
              </div>
            </div>
          )}

          <p className="text-xs text-cinza-texto">
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
    <Card
      as={Link}
      to={`/aluno/treino/${exercicio.id}`}
      principal
      className="gap-0! p-4! transition-transform active:translate-x-0.5 active:translate-y-0.5"
    >
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-sm font-bold text-noite break-words">{exercicio.titulo}</span>
        {exercicio.resolvido && <Badge color="green">resolvido</Badge>}
        <span className="ml-auto text-xs text-cinza-texto">
          {exercicio.tentativas} tentativa{exercicio.tentativas !== 1 ? 's' : ''}
        </span>
      </div>
      <p className="text-xs text-cinza-texto mt-1">{shortError(exercicio.error_category)}</p>
    </Card>
  )
}
