import { Check } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getErrosRecorrentes, getProgresso } from '../../api/aluno'
import Badge from '../../components/Badge'
import BarList from '../../components/BarList'
import Spinner from '../../components/Spinner'
import Card from '../../components/ui/Card'
import PainelDestaque from '../../components/ui/PainelDestaque'
import Progresso from '../../components/ui/Progresso'
import RotuloSecao from '../../components/ui/RotuloSecao'
import { dataCurta } from '../../utils/datas'
import { shortError } from '../../utils/errorLabels'

const TENDENCIA = {
  melhorando: { label: 'melhorando', color: 'green' },
  piorando: { label: 'em alta', color: 'red' },
  estavel: { label: 'estável', color: 'gray' },
}

function Kpi({ label, value, sub }) {
  return (
    <Card className="gap-0!">
      <RotuloSecao>{label}</RotuloSecao>
      <p className="mt-1 font-titulo text-2xl font-extrabold text-noite">{value ?? '—'}</p>
      {sub && <p className="text-xs text-cinza-texto mt-0.5 break-words">{sub}</p>}
    </Card>
  )
}

const TITULO_DO_MODO = { prova: 'Provas', treino: 'Listas' }

function ProgressoDoModo({ item }) {
  const pct = item.total_questoes ? Math.round(item.questoes_resolvidas / item.total_questoes * 100) : 0
  return (
    <Card>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3">
        <h3 className="titulo-card">{TITULO_DO_MODO[item.modo] ?? item.modo}</h3>
        <p className="text-xs text-cinza-texto">
          {item.atividades_concluidas} de {item.total_atividades} concluída{item.total_atividades !== 1 ? 's' : ''}
        </p>
      </div>
      {item.total_questoes > 0 ? (
        <>
          <Progresso valor={pct} rotulo={`${TITULO_DO_MODO[item.modo] ?? item.modo}: questões resolvidas`} />
          <p className="text-xs text-cinza-texto">
            {item.questoes_resolvidas} de {item.total_questoes} questões resolvidas
          </p>
        </>
      ) : (
        <p className="text-xs text-cinza-texto">
          {item.modo === 'treino' ? 'Nenhuma lista na sua turma ainda.' : 'Nenhuma prova na sua turma ainda.'}
        </p>
      )}
    </Card>
  )
}

function semanaLabel(iso) {
  const d = new Date(`${iso}T00:00:00`)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

export default function ProgressoPage() {
  const [progresso, setProgresso] = useState(null)
  const [erros, setErros] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getProgresso(), getErrosRecorrentes()])
      .then(([p, e]) => { setProgresso(p.data); setErros(e.data) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-violeta" />
      </div>
    )
  }

  const semSubmissao = progresso.total_tentativas === 0
  const superados = erros.superados ?? []
  const noTreino = progresso.tentativas_no_treino > 0
    ? `, ${progresso.tentativas_no_treino} no treino`
    : ''

  return (
    <div className="space-y-8">
      <div>
        <h1 className="titulo-pagina">Meu progresso</h1>
        <p className="text-sm text-cinza-texto mt-0.5">
          O que suas tentativas mostram sobre o que você já domina e o que ainda trava.
        </p>
      </div>

      {semSubmissao ? (
        <Card className="border-dashed border-noite/30! text-center p-10!">
          <p className="text-sm text-cinza-texto">Você ainda não enviou nenhuma tentativa.</p>
          <p className="text-xs text-cinza-texto">Resolva uma questão e o acompanhamento começa aqui.</p>
        </Card>
      ) : (
        <>
          <PainelDestaque>
            <div className="pr-0 sm:pr-24">
              <p className="font-titulo font-extrabold text-5xl break-words">{superados.length}</p>
              <p className="mt-1 font-titulo font-extrabold text-[13px] uppercase tracking-[0.1em] text-white/80">Erros superados</p>
              <p className="mt-1 text-sm text-white/80">
                erros que pararam de aparecer · {progresso.total_tentativas} tentativas{noTreino}
              </p>
            </div>
          </PainelDestaque>

          <div className="grid gap-3 grid-cols-1 sm:grid-cols-3">
            <Kpi
              label="Questões resolvidas"
              value={`${progresso.questoes_resolvidas}/${progresso.total_questoes}`}
              sub={`${progresso.atividades_concluidas} de ${progresso.total_atividades} atividades concluídas`}
            />
            <Kpi
              label="Tentativas até acertar"
              value={progresso.tentativas_por_questao_resolvida ?? '—'}
              sub="média nas questões e treinos que você resolveu"
            />
            <Kpi
              label="Acertos de primeira"
              value={progresso.acertos_de_primeira}
              sub="questões e treinos resolvidos no primeiro envio"
            />
          </div>

          {progresso.por_modo?.length > 0 && (
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
              {progresso.por_modo.map(item => <ProgressoDoModo key={item.modo} item={item} />)}
            </div>
          )}

          {progresso.evolucao.length > 0 && (
            <Card>
              <h2 className="titulo-card">Semana a semana</h2>
              <p className="text-xs text-cinza-texto">
                Tentativas enviadas e o que você resolveu pela primeira vez, nas provas, nas listas e no treino.
              </p>
              <BarList
                items={progresso.evolucao.map(p => ({
                  label: semanaLabel(p.periodo),
                  value: p.tentativas,
                  display: (
                    <span aria-label={`${p.tentativas} tentativas, ${p.resolvidas} resolvidas`}>
                      {p.tentativas} · {p.resolvidas}<Check className="w-3.5 h-3.5 inline" aria-hidden="true" />
                    </span>
                  ),
                  title: `Semana de ${semanaLabel(p.periodo)}`,
                }))}
              />
            </Card>
          )}
        </>
      )}

      <div className="space-y-3">
        <RotuloSecao as="h2">Erros que se repetem</RotuloSecao>
        <p className="text-xs text-cinza-texto">
          {erros.total_com_erro} de {erros.total_submissoes} tentativas tiveram algum erro, somando provas, listas e treino.
        </p>

        {erros.erros.length === 0 ? (
          <Card className="border-dashed border-noite/30! text-center p-8!">
            <p className="text-sm text-cinza-texto">
              {superados.length > 0 ? 'Nenhum erro se repetindo agora.' : 'Nenhum erro registrado ainda.'}
            </p>
          </Card>
        ) : (
          <div className="space-y-3">
            {erros.erros.map(e => {
              const tendencia = TENDENCIA[e.tendencia] ?? TENDENCIA.estavel
              return (
                <Card key={e.error_category} className="gap-2!">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-bold text-noite" title={e.error_category}>
                        {shortError(e.error_category)}
                      </span>
                      <Badge color={tendencia.color}>{tendencia.label}</Badge>
                    </div>
                    <span className="text-xs text-cinza-texto">
                      {e.total}×{e.no_treino > 0 ? ` · ${e.no_treino} no treino` : ''} · {e.recentes} nas últimas tentativas
                    </span>
                  </div>

                  {e.o_que_fazer && (
                    <div className="rounded-botao bg-lavanda border-2 border-violeta px-4 py-2.5">
                      <p className="text-xs text-violeta">{e.o_que_fazer}</p>
                    </div>
                  )}

                  {e.questoes.length > 0 && (
                    <p className="text-xs text-cinza-texto break-words">Aconteceu em: {e.questoes.join(', ')}</p>
                  )}
                </Card>
              )
            })}
          </div>
        )}
      </div>

      {superados.length > 0 && (
        <div className="space-y-3">
          <RotuloSecao as="h2">Erros que você superou</RotuloSecao>
          <p className="text-xs text-cinza-texto">
            Você acertou um treino feito para eles depois da última vez que apareceram. Se um voltar, ele sobe para a lista de cima.
          </p>
          <Card className="p-0! gap-0! divide-y-2 divide-noite/10 overflow-hidden">
            {superados.map(s => (
              <div key={s.error_category} className="flex flex-wrap items-center gap-2 px-5 py-3">
                <span className="text-sm text-noite" title={s.error_category}>
                  {shortError(s.error_category)}
                </span>
                <Badge color="green">superado</Badge>
                <span className="ml-auto text-xs text-cinza-texto">
                  em {dataCurta(s.superado_em)} · apareceu {s.total}×
                </span>
              </div>
            ))}
          </Card>
        </div>
      )}
    </div>
  )
}
