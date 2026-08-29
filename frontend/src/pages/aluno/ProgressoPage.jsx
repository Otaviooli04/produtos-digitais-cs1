import { useEffect, useState } from 'react'
import { getErrosRecorrentes, getProgresso } from '../../api/aluno'
import Badge from '../../components/Badge'
import BarList from '../../components/BarList'
import Spinner from '../../components/Spinner'
import { shortError } from '../../utils/errorLabels'

const TENDENCIA = {
  melhorando: { label: 'melhorando', color: 'green' },
  piorando: { label: 'em alta', color: 'red' },
  estavel: { label: 'estável', color: 'gray' },
}

function Kpi({ label, value, sub }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
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
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  const semSubmissao = progresso.total_tentativas === 0

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Meu progresso</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          O que suas tentativas mostram sobre o que você já domina e o que ainda trava.
        </p>
      </div>

      {semSubmissao ? (
        <div className="bg-white rounded-xl border border-dashed border-gray-200 p-10 text-center">
          <p className="text-sm text-gray-500">Você ainda não enviou nenhuma tentativa.</p>
          <p className="text-xs text-gray-400 mt-1">Resolva uma questão e o acompanhamento começa aqui.</p>
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
              sub="média nas questões que você resolveu"
            />
            <Kpi
              label="Acertos de primeira"
              value={progresso.acertos_de_primeira}
              sub="questões resolvidas no primeiro envio"
            />
            <Kpi
              label="Dias seguidos"
              value={progresso.dias_seguidos}
              sub={`${progresso.total_tentativas} tentativas no total`}
            />
          </div>

          {progresso.evolucao.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">Semana a semana</h2>
              <p className="text-xs text-gray-400 mb-4">Tentativas enviadas e questões resolvidas pela primeira vez.</p>
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
        <h2 className="text-sm font-semibold text-gray-900 mb-1">Erros que se repetem</h2>
        <p className="text-xs text-gray-400 mb-3">
          {erros.total_com_erro} de {erros.total_submissoes} tentativas tiveram algum erro.
        </p>

        {erros.erros.length === 0 ? (
          <div className="bg-white rounded-xl border border-dashed border-gray-200 p-8 text-center">
            <p className="text-sm text-gray-500">Nenhum erro registrado ainda.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {erros.erros.map(e => {
              const tendencia = TENDENCIA[e.tendencia] ?? TENDENCIA.estavel
              return (
                <div key={e.error_category} className="bg-white rounded-xl border border-gray-200 p-5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900" title={e.error_category}>
                        {shortError(e.error_category)}
                      </span>
                      <Badge color={tendencia.color}>{tendencia.label}</Badge>
                    </div>
                    <span className="text-xs text-gray-400">
                      {e.total}× · {e.recentes} nas últimas tentativas
                    </span>
                  </div>

                  {e.o_que_fazer && (
                    <div className="mt-3 rounded-lg bg-blue-50 border border-blue-100 px-4 py-2.5">
                      <p className="text-xs text-blue-700">{e.o_que_fazer}</p>
                    </div>
                  )}

                  {e.questoes.length > 0 && (
                    <p className="mt-2 text-xs text-gray-400">Aconteceu em: {e.questoes.join(' · ')}</p>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
