import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getExercicio, reportarExercicio, treinar } from '../../api/aluno'
import Badge from '../../components/Badge'
import Spinner from '../../components/Spinner'
import TentativaDetalhe from '../../components/TentativaDetalhe'
import { categoriaColor, formatarData } from '../../utils/atividade'
import { shortError } from '../../utils/errorLabels'

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
    return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  }
  if (!exercicio) {
    return <p className="text-sm text-red-600">{erro || 'Exercício não encontrado.'}</p>
  }

  const anteriores = (exercicio.tentativas_lista || []).slice(resultado ? 1 : 0)

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 text-sm text-gray-400">
        <Link to="/aluno/treino" className="hover:text-gray-600">Treino</Link>
        <span>›</span>
        <span className="text-gray-600 truncate">{exercicio.titulo}</span>
      </div>

      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-semibold text-gray-900">{exercicio.titulo}</h1>
          {exercicio.resolvido && <Badge color="green">resolvido</Badge>}
        </div>
        <p className="text-xs text-gray-400 mt-1">
          Treino para {shortError(exercicio.error_category)} · tentativas ilimitadas · não vale nota
        </p>
      </div>

      {exercicio.reaproveitado && (
        <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-2.5 text-xs text-blue-800">
          Este exercício já estava aberto na sua trilha. Resolver o que está pendente
          vale mais do que acumular exercício novo.
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Enunciado</h2>
        <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{exercicio.enunciado}</p>
        <div className="flex flex-wrap gap-2 mt-3 text-xs text-gray-400">
          <span>{exercicio.total_testes} caso{exercicio.total_testes !== 1 ? 's' : ''} de teste</span>
          {exercicio.required_structures?.length > 0 && (
            <span>· obrigatório: {exercicio.required_structures.join(', ')}</span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">Seu código em C</h2>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          rows={14}
          className="w-full font-mono text-xs bg-gray-900 text-gray-100 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-purple-400"
        />
        {erro && <p className="mt-2 text-xs text-red-600">{erro}</p>}
        <div className="flex items-center gap-2 mt-3">
          <button
            onClick={enviar}
            disabled={enviando || !code.trim()}
            className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors"
          >
            {enviando && <Spinner className="w-4 h-4" />}
            {enviando ? 'Executando…' : 'Enviar tentativa'}
          </button>
          <button
            onClick={() => setReportando(r => !r)}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            Este exercício está errado
          </button>
        </div>

        {reportando && (
          <div className="mt-3 rounded-lg border border-gray-200 p-3">
            <p className="text-xs text-gray-500 mb-2">
              O exercício foi gerado automaticamente e não passou pelo professor. Diga
              o que está errado que ele sai da sua trilha.
            </p>
            <input
              value={motivo}
              onChange={(e) => setMotivo(e.target.value)}
              placeholder="Ex.: o enunciado não diz o formato da saída."
              className="w-full text-sm rounded-lg border border-gray-200 px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-purple-200"
            />
            <button
              onClick={reportar}
              className="mt-2 text-xs px-3 py-1.5 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
            >
              Tirar da trilha
            </button>
          </div>
        )}
      </div>

      {resultado && (
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Resultado</h2>
          <TentativaDetalhe tentativa={resultado.tentativa} structureCheck={resultado.structure_check} />
        </div>
      )}

      {anteriores.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Tentativas anteriores
          </h2>
          <div className="space-y-2">
            {anteriores.map(t => (
              <details key={t.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <summary className="flex items-center gap-2 px-5 py-3 cursor-pointer hover:bg-gray-50 transition-colors">
                  <span className="text-xs text-gray-400">#{t.attempt_number}</span>
                  <Badge color={categoriaColor(t.error_category)}>{t.error_category}</Badge>
                  <span className="text-xs text-gray-400 truncate">{formatarData(t.submitted_at)}</span>
                  {t.tests_total > 0 && (
                    <span className="ml-auto text-xs text-gray-400">
                      {t.tests_passed}/{t.tests_total} testes
                    </span>
                  )}
                </summary>
                <div className="border-t border-gray-100 p-4 bg-gray-50">
                  <TentativaDetalhe tentativa={t} mostrarCodigo />
                </div>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
