import { shortError } from '../utils/errorLabels'
import { comTipo } from '../utils/atividade'

const TENDENCIA = {
  caindo: { rotulo: 'caindo', classe: 'text-sucesso bg-sucesso-fundo border-sucesso/30', seta: '↓' },
  subindo: { rotulo: 'voltando', classe: 'text-erro bg-erro-fundo border-erro/30', seta: '↑' },
  estavel: { rotulo: 'estável', classe: 'text-cinza-texto bg-lavanda border-noite/20', seta: '→' },
}

/**
 * A dificuldade que atravessa a turma de uma prova para a outra.
 *
 * "Erros mais frequentes" soma tudo e responde qual é o erro mais comum da
 * turma. Esta tela responde outra coisa: se ele está caindo ou voltando ao
 * longo do semestre, que é o que decide se vale retomar o assunto em aula.
 *
 * A comparação é por proporção dos envios com erro de cada prova. Prova com
 * mais envios teria mais ocorrências de tudo, e a dificuldade pareceria crescer
 * sem ter crescido.
 */
export default function TrajetoriaDeErros({ trajetoria }) {
  if (!trajetoria?.length) return null

  return (
    <div className="bg-white rounded-xl border border-noite/20 p-5">
      <h2 className="text-sm font-semibold text-cinza-texto">De uma atividade para a outra</h2>
      <p className="text-xs text-cinza-texto mt-0.5 mb-4">
        Dificuldades que apareceram em mais de uma prova ou lista, pela fatia que ocupam
        dos envios com erro de cada uma.
      </p>

      <div className="space-y-4">
        {trajetoria.slice(0, 6).map((t) => {
          const info = TENDENCIA[t.tendencia] ?? TENDENCIA.estavel
          return (
            <div key={t.error_category}>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-sm text-cinza-texto truncate" title={t.error_category}>
                  {shortError(t.error_category)}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded border shrink-0 ${info.classe}`}>
                  {info.seta} {info.rotulo}
                </span>
                <span className="ml-auto text-xs text-cinza-texto shrink-0">
                  {t.provas} atividades
                </span>
              </div>

              <div className="flex items-end gap-1.5">
                {t.pontos.map((p) => (
                  <div key={p.exam_id} className="flex-1 min-w-0" title={`${comTipo(p.modo, p.titulo)}: ${p.proporcao}% dos envios com erro`}>
                    <div className="h-16 flex items-end">
                      <div
                        className="w-full rounded-t bg-violeta/30"
                        style={{ height: `${Math.max(4, p.proporcao)}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-cinza-texto mt-1 truncate">{comTipo(p.modo, p.titulo)}</p>
                    <p className="text-[10px] text-cinza-texto">{p.proporcao}%</p>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
