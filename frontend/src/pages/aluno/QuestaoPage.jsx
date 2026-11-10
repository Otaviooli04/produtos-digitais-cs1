import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, ChevronDown } from 'lucide-react'
import { getAtividade, getTentativas, submeterResposta } from '../../api/aluno'
import Badge from '../../components/Badge'
import RitmoDaTentativa from '../../components/RitmoDaTentativa'
import Spinner from '../../components/Spinner'
import TentativaDetalhe from '../../components/TentativaDetalhe'
import Botao from '../../components/ui/Botao'
import Card from '../../components/ui/Card'
import RotuloSecao from '../../components/ui/RotuloSecao'
import { categoriaColor, formatarData } from '../../utils/atividade'
import CodeTextarea from '../../components/CodeTextarea'

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
    <div className="bg-white rounded-botao border-2 border-noite overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full min-h-11 flex items-center justify-between gap-3 px-5 py-3 hover:bg-lavanda transition-colors text-left"
      >
        <span className="flex flex-wrap items-center gap-x-2 gap-y-1 min-w-0">
          <span className="text-xs text-cinza-texto shrink-0">#{tentativa.attempt_number}</span>
          <Badge color={categoriaColor(tentativa.error_category)}>{tentativa.error_category}</Badge>
          <span className="text-xs text-cinza-texto break-words">{formatarData(tentativa.submitted_at)}</span>
        </span>
        <span className="flex items-center gap-1 text-xs text-cinza-texto shrink-0">
          {tentativa.tests_total > 0 && `${tentativa.tests_passed}/${tentativa.tests_total} testes · `}
          {aberto ? 'ocultar' : 'ver'}
          <ChevronDown className={`w-4 h-4 transition-transform ${aberto ? 'rotate-180' : ''}`} aria-hidden="true" />
        </span>
      </button>
      <div className={`border-t-2 border-noite p-4 bg-lavanda${aberto ? '' : ' hidden'}`}>
        <TentativaDetalhe tentativa={tentativa} mostrarCodigo />
      </div>
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
        <Spinner className="w-6 h-6 text-violeta" />
      </div>
    )
  }

  if (!questao) {
    return <p className="text-sm text-erro">{error || 'Questão não encontrada.'}</p>
  }

  const anteriores = (historico?.tentativas || []).filter(
    t => t.submission_id !== resultado?.tentativa?.submission_id)

  return (
    <div className="space-y-6">
      <div>
        <Link
          to={`/aluno/atividades/${examId}`}
          className="inline-flex items-center gap-1 min-h-11 text-sm font-bold text-cinza-texto hover:text-noite"
        >
          <ArrowLeft className="w-4 h-4 shrink-0" aria-hidden="true" />
          <span className="break-words">{atividade.titulo}</span>
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <h1 className="titulo-pagina">Questão {questao.number}</h1>
          {questao.resolvida && <Badge color="green">Resolvida</Badge>}
          {questao.tentativas_restantes != null && (
            <Badge color={questao.tentativas_restantes > 0 ? 'gray' : 'red'}>
              {questao.tentativas_restantes} tentativa(s) restante(s)
            </Badge>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 items-start">
        <div className="min-w-0 space-y-6 lg:col-start-1 lg:row-start-1">
          <Card principal>
            <p className="text-sm text-cinza-texto leading-relaxed whitespace-pre-wrap break-words">{questao.statement}</p>
            <div className="space-y-1">
              {questao.required_structures?.length > 0 && (
                <p className="text-xs text-cinza-texto break-words">
                  Estruturas obrigatórias: <span className="font-bold text-violeta">{questao.required_structures.join(', ')}</span>
                </p>
              )}
              {questao.forbidden_structures?.length > 0 && (
                <p className="text-xs text-erro break-words">Proibido: {questao.forbidden_structures.join(', ')}</p>
              )}
              {questao.required_functions?.length > 0 && (
                <p className="text-xs text-cinza-texto break-words">
                  Funções exigidas: <span className="font-bold text-violeta">{questao.required_functions.map(formatarFuncao).join(', ')}</span>
                </p>
              )}
            </div>
          </Card>
        </div>

        <div className="min-w-0 space-y-6 lg:col-start-2 lg:row-start-1 lg:row-span-2">
          <Card>
            <label className="block text-xs font-bold text-cinza-texto">Seu código em C</label>
            <CodeTextarea
              rows={18}
              value={code}
              onChange={e => setCode(e.target.value)}
              spellCheck={false}
              disabled={!podeEnviar}
              className="w-full text-sm font-mono bg-noite text-codigo-texto caret-white rounded-botao border-2 border-noite px-3 py-2.5 focus-visible:outline-codigo-sucesso resize-y disabled:opacity-60 max-h-[55vh] sm:max-h-none"
            />

            {!podeEnviar && (
              <p className="text-xs text-aviso">
                {semTentativas
                  ? 'Você usou todas as tentativas desta questão.'
                  : atividade.situacao === 'agendada'
                    ? 'Esta atividade ainda não abriu.'
                    : 'Esta atividade já encerrou.'}
              </p>
            )}

            {error && (
              <div className="rounded-botao bg-erro-fundo border-2 border-erro px-4 py-2.5 text-sm text-erro">
                {error}
              </div>
            )}

            <Botao
              onClick={handleEnviar}
              disabled={enviando || !podeEnviar || !code.trim()}
              className="w-full"
            >
              {enviando && <Spinner className="w-4 h-4" />}
              {enviando ? 'Avaliando…' : questao.tentativas > 0 ? 'Enviar nova tentativa' : 'Enviar resposta'}
            </Botao>
          </Card>

          {resultado && (
            <div className="space-y-3">
              <RotuloSecao as="h2">Resultado</RotuloSecao>
              <RitmoDaTentativa
                avanco={resultado.avanco}
                sugerirPausa={resultado.sugerir_pausa}
                semCasos={resultado.tentativa.tests_total === 0}
              />
              <TentativaDetalhe
                tentativa={resultado.tentativa}
                functionCheck={resultado.function_check}
              />
              {vizinhas.proxima && resultado.resolvida && (
                <Botao
                  onClick={() => navigate(`/aluno/atividades/${examId}/questoes/${vizinhas.proxima}`)}
                  className="w-full"
                >
                  Ir para a questão {vizinhas.proxima}
                </Botao>
              )}
            </div>
          )}
        </div>

        {anteriores.length > 0 && (
          <div className="min-w-0 space-y-6 lg:col-start-1 lg:row-start-2">
            <div className="space-y-2">
              <RotuloSecao as="h2">
                Tentativas anteriores ({anteriores.length})
              </RotuloSecao>
              {anteriores.map(t => (
                <ItemHistorico
                  key={t.submission_id}
                  tentativa={t}
                  aberto={!!abertos[t.submission_id]}
                  onToggle={() => setAbertos(a => ({ ...a, [t.submission_id]: !a[t.submission_id] }))}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap justify-between gap-2 pt-2">
        {vizinhas.anterior ? (
          <Botao
            variante="secundario"
            to={`/aluno/atividades/${examId}/questoes/${vizinhas.anterior}`}
          >
            <ArrowLeft className="w-4 h-4" aria-hidden="true" />
            Questão {vizinhas.anterior}
          </Botao>
        ) : <span />}
        {vizinhas.proxima && (
          <Botao
            variante="secundario"
            to={`/aluno/atividades/${examId}/questoes/${vizinhas.proxima}`}
          >
            Questão {vizinhas.proxima}
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </Botao>
        )}
      </div>
    </div>
  )
}
