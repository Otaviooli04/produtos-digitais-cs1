import Badge from './Badge'
import FunctionCheckCard from './FunctionCheckCard'
import AjudaEmEtapas from './AjudaEmEtapas'
import { categoriaColor, formatarData } from '../utils/atividade'

/**
 * Resultado de uma tentativa como o aluno precisa ler: o que aconteceu, por que
 * e o que fazer. Mesmo bloco serve para o envio recém-feito e para o histórico.
 */
export default function TentativaDetalhe({
  tentativa, functionCheck = null, mostrarCodigo = false, permitirAjuda = true,
}) {
  if (!tentativa) return null

  // A ajuda em etapas vale para prova e lista, que têm `submission_id` e cache
  // próprio. A trilha fica sem, porque não tem `submission_id`. Falha técnica
  // também não pede ajuda: a tentativa nem foi corrigida.
  const podePedirAjuda = permitirAjuda && tentativa.submission_id != null
  const temErro = tentativa.error_category && tentativa.error_category !== 'Correto'
    && tentativa.error_category !== 'Erro Desconhecido'

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-noite/20 bg-white p-5">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Badge color={categoriaColor(tentativa.error_category)}>
            {tentativa.error_category || 'Sem diagnóstico'}
          </Badge>
          <span className="text-xs text-cinza-texto">
            Tentativa {tentativa.attempt_number} · {formatarData(tentativa.submitted_at)}
          </span>
        </div>
        <p className="text-sm text-cinza-texto">{tentativa.pedagogical_diagnosis}</p>
        {tentativa.actionable_feedback && (
          <div className="mt-3 rounded-lg bg-lavanda border border-violeta/15 px-4 py-2.5">
            <p className="text-xs font-medium text-violeta mb-0.5">O que fazer</p>
            <p className="text-xs text-violeta">{tentativa.actionable_feedback}</p>
          </div>
        )}

        {temErro && podePedirAjuda && (
          <AjudaEmEtapas key={tentativa.submission_id} tentativa={tentativa} />
        )}
      </div>

      {/* O retorno do professor vem em cartão próprio, fora do bloco do
          diagnóstico, para não se confundir com o que a máquina escreveu. O aluno
          não sabe (nem precisa saber) que o texto foi escrito para um grupo. */}
      {tentativa.resposta_do_professor && (
        <div className="rounded-xl border border-sucesso/30 bg-sucesso-fundo p-5">
          <div className="flex items-center gap-2 mb-1.5">
            <svg className="w-4 h-4 text-sucesso" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <h3 className="text-sm font-medium text-sucesso">Retorno do seu professor</h3>
            {tentativa.resposta_do_professor_em && (
              <span className="text-xs text-sucesso/70">
                {formatarData(tentativa.resposta_do_professor_em)}
              </span>
            )}
          </div>
          <p className="text-sm text-sucesso leading-relaxed whitespace-pre-wrap break-words">
            {tentativa.resposta_do_professor}
          </p>
        </div>
      )}

      {functionCheck && !functionCheck.compliant && <FunctionCheckCard check={functionCheck} />}

      {tentativa.compile_error && (
        <div className="rounded-xl border border-noite/20 bg-white p-5">
          <h3 className="text-sm font-medium text-cinza-texto mb-2">Erro de compilação</h3>
          <pre className="text-xs font-mono bg-noite rounded-lg p-3 overflow-x-auto text-codigo-erro whitespace-pre-wrap">{tentativa.compile_error}</pre>
        </div>
      )}

      {tentativa.warnings && (
        <div className="rounded-xl border border-noite/20 bg-white p-5">
          <h3 className="text-sm font-medium text-cinza-texto mb-2">Avisos do compilador</h3>
          <pre className="text-xs font-mono bg-noite rounded-lg p-3 overflow-x-auto text-codigo-aviso whitespace-pre-wrap">{tentativa.warnings}</pre>
        </div>
      )}

      {tentativa.test_results?.length > 0 && (
        <div className="rounded-xl border border-noite/20 bg-white p-5">
          <h3 className="text-sm font-medium text-cinza-texto mb-3">
            Testes: {tentativa.tests_passed}/{tentativa.tests_total} passaram
          </h3>
          <div className="space-y-2">
            {tentativa.test_results.map((tr, i) => (
              <div
                key={i}
                className={`rounded-lg border px-4 py-3 ${tr.passed ? 'bg-sucesso-fundo border-sucesso/30' : 'bg-erro-fundo border-erro/30'}`}
              >
                <p className={`text-xs font-semibold mb-1.5 ${tr.passed ? 'text-sucesso' : 'text-erro'}`}>
                  {tr.passed ? '✓ Correto' : '✗ Incorreto'}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono break-words">
                  <div><span className="text-cinza-texto">entrada: </span><span className="text-cinza-texto">{tr.input || '(vazia)'}</span></div>
                  <div><span className="text-cinza-texto">esperado: </span><span className="text-cinza-texto">{tr.expected_output}</span></div>
                  <div><span className="text-cinza-texto">obtido: </span><span className={tr.passed ? 'text-sucesso' : 'text-erro'}>{tr.actual_output}</span></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {mostrarCodigo && tentativa.code && (
        <div className="rounded-xl border border-noite/20 bg-white p-5">
          <h3 className="text-sm font-medium text-cinza-texto mb-2">Código enviado</h3>
          <pre className="text-xs font-mono bg-noite rounded-lg p-3 overflow-x-auto text-codigo-texto whitespace-pre">{tentativa.code}</pre>
        </div>
      )}
    </div>
  )
}
