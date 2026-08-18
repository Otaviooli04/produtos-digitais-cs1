import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getAtividade, getTentativas, submeterResposta } from '../../api/aluno'
import Badge from '../../components/Badge'
import Spinner from '../../components/Spinner'
import TentativaDetalhe from '../../components/TentativaDetalhe'
import { categoriaColor, formatarData } from '../../utils/atividade'

const MODELO = '#include <stdio.h>\n\nint main() {\n    \n    return 0;\n}'

function formatarFuncao(fn) {
  const tags = []
  if (fn.requires_recursion) tags.push('recursiva')
  if (fn.requires_pointer_param) tags.push('ponteiro')
  const params = fn.param_count != null ? `(${fn.param_count} param.)` : ''
  return `${fn.name}${params}${tags.length ? ` [${tags.join(', ')}]` : ''}`
}

function ItemHistorico({ tentativa, aberto, onToggle }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-3 px-5 py-3 hover:bg-gray-50 transition-colors text-left"
      >
        <span className="flex items-center gap-2 min-w-0">
          <span className="text-xs text-gray-400 shrink-0">#{tentativa.attempt_number}</span>
          <Badge color={categoriaColor(tentativa.error_category)}>{tentativa.error_category}</Badge>
          <span className="text-xs text-gray-400 truncate">{formatarData(tentativa.submitted_at)}</span>
        </span>
        <span className="text-xs text-gray-400 shrink-0">
          {tentativa.tests_total > 0 && `${tentativa.tests_passed}/${tentativa.tests_total} testes · `}
          {aberto ? 'ocultar' : 'ver'}
        </span>
      </button>
      {aberto && (
        <div className="border-t border-gray-100 p-4 bg-gray-50">
          <TentativaDetalhe tentativa={tentativa} mostrarCodigo />
        </div>
      )}
    </div>
  )
}

/**
 * A questão é remontada a cada troca de número (key na rota interna), então todo
 * o estado local — código digitado, resultado, histórico aberto — nasce limpo
 * sem precisar de efeito de reset.
 */
export default function QuestaoPage() {
  const { examId, numero } = useParams()
  return <QuestaoConteudo key={`${examId}/${numero}`} examId={examId} numero={numero} />
}

function QuestaoConteudo({ examId, numero }) {
  const navigate = useNavigate()
  const [atividade, setAtividade] = useState(null)
  const [historico, setHistorico] = useState(null)
  const [loading, setLoading] = useState(true)
  const [code, setCode] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState('')
  const [abertos, setAbertos] = useState({})

  const carregar = () => Promise.all([getAtividade(examId), getTentativas(examId, numero)])
    .then(([a, h]) => {
      setAtividade(a.data)
      setHistorico(h.data)
      const questao = a.data.questoes.find(q => q.number === numero)
      setCode(questao?.ultimo_codigo || MODELO)
    })
    .catch(err => setError(err.response?.data?.detail || 'Questão não encontrada.'))
    .finally(() => setLoading(false))

  useEffect(() => {
    carregar()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const questao = useMemo(
    () => atividade?.questoes.find(q => q.number === numero),
    [atividade, numero],
  )

  const vizinhas = useMemo(() => {
    if (!atividade) return { anterior: null, proxima: null }
    const nums = atividade.questoes.map(q => q.number)
    const i = nums.indexOf(numero)
    return { anterior: nums[i - 1] ?? null, proxima: nums[i + 1] ?? null }
  }, [atividade, numero])

  const semTentativas = questao?.tentativas_restantes === 0
  const podeEnviar = atividade?.aberta && !semTentativas

  const handleEnviar = async () => {
    if (!code.trim()) { setError('Escreva o código antes de enviar.'); return }
    setError('')
    setEnviando(true)
    setResultado(null)
    try {
      const { data } = await submeterResposta(examId, numero, code)
      setResultado(data)
      const [a, h] = await Promise.all([getAtividade(examId), getTentativas(examId, numero)])
      setAtividade(a.data)
      setHistorico(h.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Não foi possível enviar. Tente de novo.')
    } finally {
      setEnviando(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  if (!questao) {
    return <p className="text-sm text-red-600">{error || 'Questão não encontrada.'}</p>
  }

  const anteriores = (historico?.tentativas || []).filter(
    t => t.submission_id !== resultado?.tentativa?.submission_id)

  return (
    <div className="space-y-5">
      <div>
        <Link to={`/aluno/atividades/${examId}`} className="text-xs text-gray-400 hover:text-gray-600">
          ← {atividade.titulo}
        </Link>
        <div className="mt-2 flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-semibold text-gray-900">Questão {questao.number}</h1>
          {questao.resolvida && <Badge color="green">Resolvida</Badge>}
          {questao.tentativas_restantes != null && (
            <Badge color={questao.tentativas_restantes > 0 ? 'gray' : 'red'}>
              {questao.tentativas_restantes} tentativa(s) restante(s)
            </Badge>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{questao.statement}</p>
        <div className="mt-3 space-y-1">
          {questao.required_structures?.length > 0 && (
            <p className="text-xs text-gray-400">
              Estruturas obrigatórias: <span className="text-purple-600">{questao.required_structures.join(', ')}</span>
            </p>
          )}
          {questao.forbidden_structures?.length > 0 && (
            <p className="text-xs text-red-400">Proibido: {questao.forbidden_structures.join(', ')}</p>
          )}
          {questao.required_functions?.length > 0 && (
            <p className="text-xs text-gray-400">
              Funções exigidas: <span className="text-purple-600">{questao.required_functions.map(formatarFuncao).join(', ')}</span>
            </p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Seu código em C</label>
        <textarea
          rows={18}
          value={code}
          onChange={e => setCode(e.target.value)}
          spellCheck={false}
          disabled={!podeEnviar}
          className="w-full text-sm font-mono rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-y bg-gray-50 disabled:opacity-60"
        />

        {!podeEnviar && (
          <p className="mt-2 text-xs text-amber-600">
            {semTentativas
              ? 'Você usou todas as tentativas desta questão.'
              : atividade.situacao === 'agendada'
                ? 'Esta atividade ainda não abriu.'
                : 'Esta atividade já encerrou.'}
          </p>
        )}

        {error && (
          <div className="mt-3 rounded-lg bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">
            {error}
          </div>
        )}

        <button
          onClick={handleEnviar}
          disabled={enviando || !podeEnviar || !code.trim()}
          className="mt-4 w-full inline-flex items-center justify-center gap-2 text-sm px-4 py-3 rounded-xl bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors font-medium"
        >
          {enviando && <Spinner className="w-4 h-4" />}
          {enviando ? 'Avaliando…' : questao.tentativas > 0 ? 'Enviar nova tentativa' : 'Enviar resposta'}
        </button>
      </div>

      {resultado && (
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-900">Resultado</h2>
          <TentativaDetalhe
            tentativa={resultado.tentativa}
            functionCheck={resultado.function_check}
          />
          {vizinhas.proxima && resultado.resolvida && (
            <button
              onClick={() => navigate(`/aluno/atividades/${examId}/questoes/${vizinhas.proxima}`)}
              className="w-full text-sm px-4 py-2.5 rounded-xl bg-purple-600 text-white hover:bg-purple-700 transition-colors"
            >
              Ir para a questão {vizinhas.proxima}
            </button>
          )}
        </div>
      )}

      {anteriores.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-sm font-semibold text-gray-900">
            Tentativas anteriores ({anteriores.length})
          </h2>
          {anteriores.map(t => (
            <ItemHistorico
              key={t.submission_id}
              tentativa={t}
              aberto={!!abertos[t.submission_id]}
              onToggle={() => setAbertos(a => ({ ...a, [t.submission_id]: !a[t.submission_id] }))}
            />
          ))}
        </div>
      )}

      <div className="flex justify-between pt-2">
        {vizinhas.anterior ? (
          <Link
            to={`/aluno/atividades/${examId}/questoes/${vizinhas.anterior}`}
            className="text-sm px-4 py-2 rounded-xl border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            ← Questão {vizinhas.anterior}
          </Link>
        ) : <span />}
        {vizinhas.proxima && (
          <Link
            to={`/aluno/atividades/${examId}/questoes/${vizinhas.proxima}`}
            className="text-sm px-4 py-2 rounded-xl border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Questão {vizinhas.proxima} →
          </Link>
        )}
      </div>
    </div>
  )
}
