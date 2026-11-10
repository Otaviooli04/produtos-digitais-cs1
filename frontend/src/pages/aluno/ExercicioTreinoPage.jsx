import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getExercicio, reportarExercicio, treinar } from '../../api/aluno'
import { ArrowLeft, ChevronRight } from 'lucide-react'
import Badge from '../../components/Badge'
import Botao from '../../components/ui/Botao'
import Card from '../../components/ui/Card'
import RotuloSecao from '../../components/ui/RotuloSecao'
import RitmoDaTentativa from '../../components/RitmoDaTentativa'
import Spinner from '../../components/Spinner'
import TentativaDetalhe from '../../components/TentativaDetalhe'
import { categoriaColor, formatarData } from '../../utils/atividade'
import { shortError } from '../../utils/errorLabels'
import CodeTextarea from '../../components/CodeTextarea'

const MODELO = '#include <stdio.h>\n\nint main() {\n    \n    return 0;\n}'

export default function ExercicioTreinoPage() {
  const { exercicioId } = useParams()
  return <Conteudo key={exercicioId} exercicioId={exercicioId} />
}

function Conteudo({ exercicioId }) {
  const navigate = useNavigate()
  const [exercicio, setExercicio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [code, setCode] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [erro, setErro] = useState('')
  const [reportando, setReportando] = useState(false)
  const [motivo, setMotivo] = useState('')

  useEffect(() => {
    getExercicio(exercicioId)
      .then(({ data }) => {
        setExercicio(data)
        const ultima = data.tentativas_lista?.[0]
        setCode(ultima?.code || MODELO)
      })
      .catch(() => setErro('Exercício não encontrado.'))
      .finally(() => setLoading(false))
  }, [exercicioId])

  const enviar = async () => {
    setErro('')
    setEnviando(true)
    try {
      const { data } = await treinar(exercicioId, code)
      setResultado(data)
      const { data: atualizado } = await getExercicio(exercicioId)
      setExercicio(atualizado)
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível enviar agora.')
    } finally {
      setEnviando(false)
    }
  }

  const reportar = async () => {
    await reportarExercicio(exercicioId, motivo)
    navigate('/aluno/treino')
  }

  if (loading) {
    return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>
  }
  if (!exercicio) {
    return <p className="text-sm text-erro">{erro || 'Exercício não encontrado.'}</p>
  }

  const anteriores = (exercicio.tentativas_lista || []).slice(resultado ? 1 : 0)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto">
        <Link to="/aluno/treino" className="inline-flex items-center gap-1 min-h-11 font-bold hover:text-noite">
          <ArrowLeft className="w-4 h-4" aria-hidden="true" />
          Treino
        </Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <span className="min-w-0 break-words">{exercicio.titulo}</span>
      </div>

      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="titulo-pagina break-words">{exercicio.titulo}</h1>
          {exercicio.resolvido && <Badge color="green">resolvido</Badge>}
        </div>
        <p className="text-xs text-cinza-texto mt-1">
          Treino para {shortError(exercicio.error_category)} · tentativas ilimitadas · não vale nota
        </p>
      </div>

      {exercicio.reaproveitado && (
        <div className="rounded-botao border-2 border-violeta bg-lavanda px-4 py-2.5 text-xs text-violeta">
          Este exercício já estava aberto na sua trilha. Resolver o que está pendente
          vale mais do que acumular exercício novo.
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2 lg:grid-rows-[auto_1fr] items-start">
        <div className="min-w-0 space-y-6 lg:col-start-1 lg:row-start-1">
          <Card principal>
            <RotuloSecao as="h2">Enunciado</RotuloSecao>
            <p className="text-sm text-cinza-texto whitespace-pre-wrap break-words leading-relaxed">{exercicio.enunciado}</p>
            <div className="flex flex-wrap gap-2 text-xs text-cinza-texto">
              <span>{exercicio.total_testes} caso{exercicio.total_testes !== 1 ? 's' : ''} de teste</span>
              {exercicio.required_structures?.length > 0 && (
                <span className="break-words">· obrigatório: {exercicio.required_structures.join(', ')}</span>
              )}
            </div>
          </Card>
        </div>

        <div className="min-w-0 space-y-6 lg:col-start-2 lg:row-start-1 lg:row-span-2">
          <Card>
            <RotuloSecao as="h2">Seu código em C</RotuloSecao>
            <CodeTextarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              spellCheck={false}
              rows={14}
              className="w-full font-mono text-xs bg-noite text-codigo-texto caret-white rounded-botao border-2 border-noite p-3 focus-visible:outline-codigo-sucesso max-h-[55vh] sm:max-h-none"
            />
            {erro && <p className="text-xs text-erro">{erro}</p>}
            <div className="flex flex-wrap items-center gap-2">
              <Botao onClick={enviar} disabled={enviando || !code.trim()}>
                {enviando && <Spinner className="w-4 h-4" />}
                {enviando ? 'Executando…' : 'Enviar tentativa'}
              </Botao>
              <button
                onClick={() => setReportando(r => !r)}
                className="min-h-11 px-2 text-xs font-bold text-cinza-texto hover:text-noite transition-colors"
              >
                Este exercício está errado
              </button>
            </div>

            {reportando && (
              <div className="rounded-botao border-2 border-noite/20 p-3">
                <p className="text-xs text-cinza-texto mb-2">
                  O exercício foi gerado automaticamente e não passou pelo professor. Diga
                  o que está errado que ele sai da sua trilha.
                </p>
                <input
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  placeholder="Ex.: o enunciado não diz o formato da saída."
                  className="campo"
                />
                <Botao variante="perigo" onClick={reportar} className="mt-2 sm:min-h-9! px-3.5! text-[13px]!">
                  Tirar da trilha
                </Botao>
              </div>
            )}
          </Card>

          {resultado && (
            <div className="space-y-3">
              <RotuloSecao as="h2">Resultado</RotuloSecao>
              <RitmoDaTentativa
                avanco={resultado.avanco}
                sugerirPausa={resultado.sugerir_pausa}
                semCasos={resultado.tentativa.tests_total === 0}
              />
              <TentativaDetalhe tentativa={resultado.tentativa} structureCheck={resultado.structure_check} />
            </div>
          )}
        </div>

        {anteriores.length > 0 && (
          <div className="min-w-0 space-y-6 lg:col-start-1 lg:row-start-2">
            <div className="space-y-2">
              <RotuloSecao as="h2">Tentativas anteriores</RotuloSecao>
              {anteriores.map(t => (
                <details key={t.id} className="bg-white rounded-botao border-2 border-noite overflow-hidden">
                  <summary className="flex flex-wrap items-center gap-2 min-h-11 px-5 py-3 cursor-pointer hover:bg-lavanda transition-colors">
                    <span className="text-xs text-cinza-texto">#{t.attempt_number}</span>
                    <Badge color={categoriaColor(t.error_category)}>{t.error_category}</Badge>
                    <span className="text-xs text-cinza-texto break-words">{formatarData(t.submitted_at)}</span>
                    {t.tests_total > 0 && (
                      <span className="ml-auto text-xs text-cinza-texto">
                        {t.tests_passed}/{t.tests_total} testes
                      </span>
                    )}
                  </summary>
                  <div className="border-t-2 border-noite p-4 bg-lavanda">
                    <TentativaDetalhe tentativa={t} mostrarCodigo />
                  </div>
                </details>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
