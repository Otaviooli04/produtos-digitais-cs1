import { shortError } from '../utils/errorLabels'
import { comTipo } from '../utils/atividade'
import Card from './ui/Card'
import Tag from './ui/Tag'

const TENDENCIA = {
  caindo: { rotulo: 'caindo', variante: 'sucesso', seta: '↓' },
  subindo: { rotulo: 'voltando', variante: 'erro', seta: '↑' },
  estavel: { rotulo: 'estável', variante: 'neutro', seta: '→' },
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
    <Card>
      <div>
        <h2 className="titulo-card">De uma atividade para a outra</h2>
        <p className="text-sm text-cinza-texto mt-1">
          Dificuldades que apareceram em mais de uma prova ou lista, pela fatia que ocupam
          dos envios com erro de cada uma.
        </p>
      </div>

      <div className="space-y-4">
        {trajetoria.slice(0, 6).map((t) => {
          const info = TENDENCIA[t.tendencia] ?? TENDENCIA.estavel
          return (
            <div key={t.error_category}>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="text-sm font-bold text-noite truncate" title={t.error_category}>
                  {shortError(t.error_category)}
                </span>
                <span className="shrink-0">
                  <Tag variante={info.variante}>{info.seta} {info.rotulo}</Tag>
                </span>
                <span className="ml-auto text-[13px] text-cinza-texto shrink-0">
                  {t.provas} atividades
                </span>
              </div>

              <div className="flex items-end gap-1.5">
                {t.pontos.map((p) => (
                  <div key={p.exam_id} className="flex-1 min-w-0" title={`${comTipo(p.modo, p.titulo)}: ${p.proporcao}% dos envios com erro`}>
                    <div className="h-16 flex items-end bg-lavanda rounded-[5px] overflow-hidden">
                      <div
                        className="w-full rounded-t-[5px] bg-violeta"
                        style={{ height: `${Math.max(4, p.proporcao)}%` }}
                      />
                    </div>
                    <p className="text-[11px] text-cinza-texto mt-1 truncate">{comTipo(p.modo, p.titulo)}</p>
                    <p className="text-[11px] font-bold text-noite">{p.proporcao}%</p>
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
