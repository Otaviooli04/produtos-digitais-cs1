import { useState } from 'react'
import Badge from './Badge'
import FunctionCheckCard from './FunctionCheckCard'
import Spinner from './Spinner'
import { explicarTentativa } from '../api/aluno'
import { categoriaColor, formatarData } from '../utils/atividade'

/**
 * Resultado de uma tentativa como o aluno precisa ler: o que aconteceu, por que
 * e o que fazer. Mesmo bloco serve para o envio recém-feito e para o histórico.
 */
export default function TentativaDetalhe({ tentativa, functionCheck = null, mostrarCodigo = false }) {
  const [explicacao, setExplicacao] = useState(tentativa?.explicacao || null)
  const [gerando, setGerando] = useState(false)
  const [erroExplicacao, setErroExplicacao] = useState('')

  if (!tentativa) return null

  const temErro = tentativa.error_category && tentativa.error_category !== 'Correto'

  const pedirExplicacao = async () => {
    setErroExplicacao('')
    setGerando(true)
    try {
      const { data } = await explicarTentativa(tentativa.submission_id)
      setExplicacao(data.explicacao)
    } catch (e) {
      setErroExplicacao(e.response?.data?.detail || 'Não foi possível gerar a explicação agora.')
    } finally {
      setGerando(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Badge color={categoriaColor(tentativa.error_category)}>
            {tentativa.error_category || 'Sem diagnóstico'}
          </Badge>
          <span className="text-xs text-gray-400">
            Tentativa {tentativa.attempt_number} · {formatarData(tentativa.submitted_at)}
          </span>
        </div>
        <p className="text-sm text-gray-700">{tentativa.pedagogical_diagnosis}</p>
        {tentativa.actionable_feedback && (
          <div className="mt-3 rounded-lg bg-blue-50 border border-blue-100 px-4 py-2.5">
            <p className="text-xs font-medium text-blue-800 mb-0.5">O que fazer</p>
            <p className="text-xs text-blue-700">{tentativa.actionable_feedback}</p>
          </div>
        )}

        {temErro && (explicacao ? (
          <div className="mt-3 rounded-lg bg-purple-50 border border-purple-100 px-4 py-2.5">
            <p className="text-xs font-medium text-purple-800 mb-0.5">Explicando o seu código</p>
            <p className="text-xs text-purple-700 whitespace-pre-wrap">{explicacao}</p>
          </div>
        ) : (
          <div className="mt-3">
            <button
              onClick={pedirExplicacao}
              disabled={gerando}
              className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border border-purple-200 text-purple-700 hover:bg-purple-50 disabled:opacity-40 transition-colors"
            >
              {gerando && <Spinner className="w-3.5 h-3.5" />}
              {gerando ? 'Analisando seu código…' : 'Explicar meu erro'}
            </button>
            {erroExplicacao && <p className="mt-1.5 text-xs text-red-600">{erroExplicacao}</p>}
          </div>
        ))}
      </div>

      {functionCheck && !functionCheck.compliant && <FunctionCheckCard check={functionCheck} />}

      {tentativa.compile_error && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Erro de compilação</h3>
          <pre className="text-xs font-mono bg-gray-900 rounded-lg p-3 overflow-x-auto text-red-400 whitespace-pre-wrap">{tentativa.compile_error}</pre>
        </div>
      )}

      {tentativa.warnings && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Avisos do compilador</h3>
          <pre className="text-xs font-mono bg-gray-900 rounded-lg p-3 overflow-x-auto text-yellow-400 whitespace-pre-wrap">{tentativa.warnings}</pre>
        </div>
      )}

      {tentativa.test_results?.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="text-sm font-medium text-gray-700 mb-3">
            Testes: {tentativa.tests_passed}/{tentativa.tests_total} passaram
          </h3>
          <div className="space-y-2">
            {tentativa.test_results.map((tr, i) => (
              <div
                key={i}
                className={`rounded-lg border px-4 py-3 ${tr.passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}
              >
                <p className={`text-xs font-semibold mb-1.5 ${tr.passed ? 'text-green-700' : 'text-red-700'}`}>
                  {tr.passed ? '✓ Correto' : '✗ Incorreto'}
                </p>
                <div className="grid sm:grid-cols-3 gap-2 text-xs font-mono">
                  <div><span className="text-gray-400">entrada: </span><span className="text-gray-700">{tr.input || '(vazia)'}</span></div>
                  <div><span className="text-gray-400">esperado: </span><span className="text-gray-700">{tr.expected_output}</span></div>
                  <div><span className="text-gray-400">obtido: </span><span className={tr.passed ? 'text-green-700' : 'text-red-700'}>{tr.actual_output}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {mostrarCodigo && tentativa.code && (
        <div className="rounded-xl border border-gray-200 bg-white p-5">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Código enviado</h3>
          <pre className="text-xs font-mono bg-gray-900 rounded-lg p-3 overflow-x-auto text-gray-100 whitespace-pre-wrap">{tentativa.code}</pre>
        </div>
      )}
    </div>
  )
}
