import { shortError } from '../utils/errorLabels'

const TENDENCIA = {
  caindo: { rotulo: 'caindo', classe: 'text-green-700 bg-green-50 border-green-200', seta: '↓' },
  subindo: { rotulo: 'voltando', classe: 'text-red-700 bg-red-50 border-red-200', seta: '↑' },
  estavel: { rotulo: 'estável', classe: 'text-gray-600 bg-gray-50 border-gray-200', seta: '→' },
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
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-sm font-semibold text-gray-700">De uma prova para a outra</h2>
      <p className="text-xs text-gray-400 mt-0.5 mb-4">
        Dificuldades que apareceram em mais de uma avaliação, pela fatia que ocupam
        dos envios com erro de cada uma.
      </p>

      <div className="space-y-4">
        {trajetoria.slice(0, 6).map((t) => {
          const info = TENDENCIA[t.tendencia] ?? TENDENCIA.estavel
          return (
            <div key={t.error_category}>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-sm text-gray-700 truncate" title={t.error_category}>
                  {shortError(t.error_category)}
                </span>
                <span className={`text-xs px-1.5 py-0.5 rounded border shrink-0 ${info.classe}`}>
                  {info.seta} {info.rotulo}
                </span>
                <span className="ml-auto text-xs text-gray-400 shrink-0">
                  {t.provas} avaliações
                </span>
              </div>

              <div className="flex items-end gap-1.5">
                {t.pontos.map((p) => (
                  <div key={p.exam_id} className="flex-1 min-w-0" title={`${p.titulo}: ${p.proporcao}% dos envios com erro`}>
                    <div className="h-16 flex items-end">
                      <div
                        className="w-full rounded-t bg-purple-300"
                        style={{ height: `${Math.max(4, p.proporcao)}%` }}
                      />
                    </div>
                    <p className="text-[10px] text-gray-500 mt-1 truncate">{p.titulo}</p>
                    <p className="text-[10px] text-gray-400">{p.proporcao}%</p>
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
