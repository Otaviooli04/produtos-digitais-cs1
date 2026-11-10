import { Check, MessageSquare, X } from 'lucide-react'
import Badge from './Badge'
import FunctionCheckCard from './FunctionCheckCard'
import AjudaEmEtapas from './AjudaEmEtapas'
import Card from './ui/Card'
import Tag from './ui/Tag'
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
      <Card>
        <div className="flex flex-wrap items-center gap-2">
          <Badge color={categoriaColor(tentativa.error_category)}>
            {tentativa.error_category || 'Sem diagnóstico'}
          </Badge>
          <span className="text-xs text-cinza-texto">
            Tentativa {tentativa.attempt_number} · {formatarData(tentativa.submitted_at)}
          </span>
        </div>
        <p className="text-sm text-cinza-texto break-words">{tentativa.pedagogical_diagnosis}</p>
        {tentativa.actionable_feedback && (
          <div className="rounded-botao bg-lavanda border-2 border-violeta px-4 py-2.5">
            <p className="text-xs font-bold text-violeta mb-0.5">O que fazer</p>
            <p className="text-xs text-violeta break-words">{tentativa.actionable_feedback}</p>
          </div>
        )}

        {temErro && podePedirAjuda && (
          <AjudaEmEtapas key={tentativa.submission_id} tentativa={tentativa} />
        )}
      </Card>

      {/* O retorno do professor vem em cartão próprio, fora do bloco do
          diagnóstico, para não se confundir com o que a máquina escreveu. O aluno
          não sabe (nem precisa saber) que o texto foi escrito para um grupo. */}
      {tentativa.resposta_do_professor && (
        <Card className="border-sucesso! bg-sucesso-fundo! gap-1.5!">
          <div className="flex flex-wrap items-center gap-2">
            <MessageSquare className="w-4 h-4 text-sucesso" aria-hidden="true" />
            <h3 className="text-sm font-bold text-sucesso">Retorno do seu professor</h3>
            {tentativa.resposta_do_professor_em && (
              <span className="text-xs text-sucesso">
                {formatarData(tentativa.resposta_do_professor_em)}
              </span>
            )}
          </div>
          <p className="text-sm text-sucesso leading-relaxed whitespace-pre-wrap break-words">
            {tentativa.resposta_do_professor}
          </p>
        </Card>
      )}

      {functionCheck && !functionCheck.compliant && <FunctionCheckCard check={functionCheck} />}

      {tentativa.compile_error && (
        <Card className="gap-2!">
          <h3 className="text-sm font-bold text-noite">Erro de compilação</h3>
          <pre className="text-xs font-mono bg-noite rounded-botao p-3 overflow-x-auto text-codigo-erro whitespace-pre-wrap">{tentativa.compile_error}</pre>
        </Card>
      )}

      {tentativa.warnings && (
        <Card className="gap-2!">
          <h3 className="text-sm font-bold text-noite">Avisos do compilador</h3>
          <pre className="text-xs font-mono bg-noite rounded-botao p-3 overflow-x-auto text-codigo-aviso whitespace-pre-wrap">{tentativa.warnings}</pre>
        </Card>
      )}

      {tentativa.test_results?.length > 0 && (
        <Card className="gap-3!">
          <h3 className="text-sm font-bold text-noite">
            Testes: {tentativa.tests_passed}/{tentativa.tests_total} passaram
          </h3>
          <div className="space-y-2">
            {tentativa.test_results.map((tr, i) => (
              <Card
                key={i}
                className={`rounded-botao! p-4! gap-2! ${tr.passed ? 'bg-sucesso-fundo! border-sucesso!' : 'bg-erro-fundo! border-erro!'}`}
              >
                <div>
                  {tr.passed
                    ? <Tag variante="sucesso"><Check className="w-3.5 h-3.5 mr-1" aria-hidden="true" />Correto</Tag>
                    : <Tag variante="erro"><X className="w-3.5 h-3.5 mr-1" aria-hidden="true" />Incorreto</Tag>}
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono break-words">
                  <div className="min-w-0"><span className="text-cinza-texto">entrada: </span><span className="text-noite">{tr.input || '(vazia)'}</span></div>
                  <div className="min-w-0"><span className="text-cinza-texto">esperado: </span><span className="text-noite">{tr.expected_output}</span></div>
                  <div className="min-w-0"><span className="text-cinza-texto">obtido: </span><span className={tr.passed ? 'text-sucesso' : 'text-erro'}>{tr.actual_output}</span></div>
                </div>
              </Card>
            ))}
          </div>
        </Card>
      )}

      {mostrarCodigo && tentativa.code && (
        <Card className="gap-2!">
          <h3 className="text-sm font-bold text-noite">Código enviado</h3>
          <pre className="text-xs font-mono bg-noite rounded-botao p-3 overflow-x-auto text-codigo-texto whitespace-pre">{tentativa.code}</pre>
        </Card>
      )}
    </div>
  )
}
