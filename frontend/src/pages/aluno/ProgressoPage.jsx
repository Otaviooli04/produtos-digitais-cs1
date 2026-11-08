import { useEffect, useState } from 'react'
import { getErrosRecorrentes, getProgresso } from '../../api/aluno'
import Badge from '../../components/Badge'
import BarList from '../../components/BarList'
import Spinner from '../../components/Spinner'
import { dataCurta } from '../../utils/datas'
import { shortError } from '../../utils/errorLabels'

const TENDENCIA = {
  melhorando: { label: 'melhorando', color: 'green' },
  piorando: { label: 'em alta', color: 'red' },
  estavel: { label: 'estável', color: 'gray' },
}

function Kpi({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-noite/20 p-5">
      <p className="text-xs text-cinza-texto font-medium uppercase tracking-wide">{label}</p>
      <p className="mt-1 text-2xl font-bold text-noite">{value ?? '—'}</p>
      {sub && <p className="text-xs text-cinza-texto mt-0.5">{sub}</p>}
    </div>
  )
}

const TITULO_DO_MODO = { prova: 'Provas', treino: 'Listas' }

function ProgressoDoModo({ item }) {
  const pct = item.total_questoes ? Math.round(item.questoes_resolvidas / item.total_questoes * 100) : 0
  return (
    <div className="bg-white rounded-xl border border-noite/20 p-5">
      <div className="flex items-baseline justify-between">
        <p className="text-sm font-semibold text-noite">{TITULO_DO_MODO[item.modo] ?? item.modo}</p>
        <p className="text-xs text-cinza-texto">
          {item.atividades_concluidas} de {item.total_atividades} concluída{item.total_atividades !== 1 ? 's' : ''}
        </p>
      </div>
      {item.total_questoes > 0 ? (
        <>
          <div className="mt-3 h-2 rounded-full bg-lavanda overflow-hidden">
            <div className="h-full rounded-full bg-violeta" style={{ width: `${pct}%` }} />
          </div>
          <p className="text-xs text-cinza-texto mt-1.5">
            {item.questoes_resolvidas} de {item.total_questoes} questões resolvidas
          </p>
        </>
      ) : (
        <p className="text-xs text-cinza-texto mt-3">
          {item.modo === 'treino' ? 'Nenhuma lista na sua turma ainda.' : 'Nenhuma prova na sua turma ainda.'}
        </p>
      )}
    </div>
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
        <h1 className="text-xl font-semibold text-noite">Meu progresso</h1>
        <p className="text-sm text-cinza-texto mt-0.5">
          O que suas tentativas mostram sobre o que você já domina e o que ainda trava.
        </p>
      </div>

      {semSubmissao ? (
        <div className="bg-white rounded-xl border border-dashed border-noite/20 p-10 text-center">
          <p className="text-sm text-cinza-texto">Você ainda não enviou nenhuma tentativa.</p>
          <p className="text-xs text-cinza-texto mt-1">Resolva uma questão e o acompanhamento começa aqui.</p>
        </div>
      ) : (
        <>
          <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
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
            <Kpi
              label="Erros superados"
              value={superados.length}
              sub={`erros que pararam de aparecer · ${progresso.total_tentativas} tentativas${noTreino}`}
            />
          </div>

          {progresso.por_modo?.length > 0 && (
            <div className="grid gap-3 grid-cols-1 sm:grid-cols-2">
              {progresso.por_modo.map(item => <ProgressoDoModo key={item.modo} item={item} />)}
            </div>
          )}

          {progresso.evolucao.length > 0 && (
            <div className="bg-white rounded-xl border border-noite/20 p-5">
              <h2 className="text-sm font-semibold text-noite mb-1">Semana a semana</h2>
              <p className="text-xs text-cinza-texto mb-4">
                Tentativas enviadas e o que você resolveu pela primeira vez, nas provas, nas listas e no treino.
              </p>
              <BarList
                items={progresso.evolucao.map(p => ({
                  label: semanaLabel(p.periodo),
                  value: p.tentativas,
                  display: `${p.tentativas} · ${p.resolvidas}✓`,
                  title: `Semana de ${semanaLabel(p.periodo)}`,
                }))}
              />
            </div>
          )}
        </>
      )}

      <div>
        <h2 className="text-sm font-semibold text-noite mb-1">Erros que se repetem</h2>
        <p className="text-xs text-cinza-texto mb-3">
          {erros.total_com_erro} de {erros.total_submissoes} tentativas tiveram algum erro, somando provas, listas e treino.
        </p>

        {erros.erros.length === 0 ? (
          <div className="bg-white rounded-xl border border-dashed border-noite/20 p-8 text-center">
            <p className="text-sm text-cinza-texto">
              {superados.length > 0 ? 'Nenhum erro se repetindo agora.' : 'Nenhum erro registrado ainda.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {erros.erros.map(e => {
              const tendencia = TENDENCIA[e.tendencia] ?? TENDENCIA.estavel
              return (
                <div key={e.error_category} className="bg-white rounded-xl border border-noite/20 p-5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-noite" title={e.error_category}>
                        {shortError(e.error_category)}
                      </span>
                      <Badge color={tendencia.color}>{tendencia.label}</Badge>
                    </div>
                    <span className="text-xs text-cinza-texto">
                      {e.total}×{e.no_treino > 0 ? ` · ${e.no_treino} no treino` : ''} · {e.recentes} nas últimas tentativas
                    </span>
                  </div>

                  {e.o_que_fazer && (
                    <div className="mt-3 rounded-lg bg-lavanda border border-violeta/15 px-4 py-2.5">
                      <p className="text-xs text-violeta">{e.o_que_fazer}</p>
                    </div>
                  )}

                  {e.questoes.length > 0 && (
                    <p className="mt-2 text-xs text-cinza-texto">Aconteceu em: {e.questoes.join(', ')}</p>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {superados.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-noite mb-1">Erros que você superou</h2>
          <p className="text-xs text-cinza-texto mb-3">
            Você acertou um treino feito para eles depois da última vez que apareceram. Se um voltar, ele sobe para a lista de cima.
          </p>
          <div className="bg-white rounded-xl border border-noite/20 divide-y divide-noite/10">
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
          </div>
        </div>
      )}
    </div>
  )
}
