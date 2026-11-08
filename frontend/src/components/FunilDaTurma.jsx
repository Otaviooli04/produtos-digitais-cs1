import { useEffect, useState } from 'react'
import { getTurmaFunil } from '../api/exam'
import Badge from './Badge'
import BarList from './BarList'
import Spinner from './Spinner'

const pct = (valor) => (valor == null ? 'sem dado' : `${valor}%`)

// A semana chega como a segunda-feira em ISO (AAAA-MM-DD).
const rotuloSemana = (iso) => {
  const [, mes, dia] = iso.split('-')
  return `${dia}/${mes}`
}

const formatarData = (iso) =>
  new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' })

// Mediana do momento de sucesso em texto curto: "45 min", "2 h 15 min", "3 dias".
const formatarDuracao = (minutos) => {
  const total = Math.floor(minutos)
  if (total < 60) return `${total} min`
  if (total < 24 * 60) {
    const horas = Math.floor(total / 60)
    const resto = total % 60
    return resto ? `${horas} h ${resto} min` : `${horas} h`
  }
  const dias = Math.floor(total / (24 * 60))
  return `${dias} ${dias === 1 ? 'dia' : 'dias'}`
}

const textoSucesso = (sucesso) => (sucesso.chegaram === 0
  ? 'Momento de sucesso: ninguém corrigiu um erro ainda.'
  : `Momento de sucesso: mediana de ${formatarDuracao(sucesso.mediana_minutos)} depois da matrícula. ${pct(sucesso.taxa_na_sessao_da_matricula)} chegaram na mesma sessão.`)

function Meta({ atingida, children }) {
  return (
    <span className={`text-xs font-medium ${atingida ? 'text-sucesso' : 'text-cinza-texto'}`}>
      {children}
    </span>
  )
}

function EtapaCard({ titulo, valor, detalhe, extra, meta, atingida }) {
  return (
    <div className="bg-white rounded-xl border border-noite/20 p-5 flex flex-col gap-1">
      <div className="flex items-baseline justify-between gap-2">
        <p className="text-xs text-cinza-texto font-medium uppercase tracking-wide">{titulo}</p>
        {meta && <Meta atingida={atingida}>{meta}</Meta>}
      </div>
      <p className="text-2xl font-bold text-noite">{valor}</p>
      {detalhe && <p className="text-xs text-cinza-texto">{detalhe}</p>}
      {extra && <p className="text-xs text-cinza-texto">{extra}</p>}
    </div>
  )
}

function AlunosEmRisco({ saude }) {
  const alunos = [
    ...saude.vermelho.map(a => ({ ...a, cor: 'red', rotulo: 'Vermelho' })),
    ...saude.amarelo.map(a => ({ ...a, cor: 'yellow', rotulo: 'Amarelo' })),
  ]
  return (
    <div className="bg-white rounded-xl border border-noite/20 p-5">
      <div className="flex items-baseline justify-between gap-2 mb-3">
        <h3 className="text-sm font-semibold text-cinza-texto">Alunos em risco</h3>
        <Meta atingida={saude.taxa_vermelho != null && saude.taxa_vermelho < saude.meta}>
          {pct(saude.taxa_vermelho)} em vermelho · meta abaixo de {saude.meta}%
        </Meta>
      </div>
      {alunos.length === 0 ? (
        <p className="text-sm text-cinza-texto">Nenhum aluno em risco agora.</p>
      ) : (
        <ul className="divide-y divide-noite/10">
          {alunos.map(a => (
            <li key={a.student_id} className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2 text-sm">
              <Badge color={a.cor}>{a.rotulo}</Badge>
              <span className="flex-1 min-w-0 truncate text-noite">{a.nome}</span>
              <span className="text-cinza-texto">{a.motivo}</span>
              <span className="text-xs text-cinza-texto">
                {a.ultimo_envio ? `último envio em ${formatarData(a.ultimo_envio)}` : 'nunca enviou'}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Painel({ funil }) {
  const { north_star: ns, aquisicao, ativacao, retencao, saude, protecao, sucesso } = funil
  const semana = retencao.ultima_completa
  const media = protecao.media_tentativas_ate_acertar
  const origem = aquisicao.por_origem
  const textoOrigem = origem.convite + origem.codigo > 0
    ? `${origem.convite} pelo convite, ${origem.codigo} pelo código.`
    : null
  return (
    <>
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="bg-white rounded-xl border border-noite/20 p-5 flex flex-col gap-1">
          <p className="text-xs text-cinza-texto font-medium uppercase tracking-wide">Erros corrigidos</p>
          <p className="text-2xl font-bold text-noite">{ns.semana_atual}</p>
          <p className="text-xs text-cinza-texto">nesta semana · {ns.total} desde o início</p>
          {ns.por_tipo && (
            <p className="text-xs text-cinza-texto mt-2">
              Onde foram corrigidos: {ns.por_tipo.provas} nas provas, {ns.por_tipo.listas} nas listas
              e {ns.por_tipo.trilha} na trilha de treino.
            </p>
          )}
        </div>
        <div className="bg-white rounded-xl border border-noite/20 p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-cinza-texto mb-4">Erros corrigidos por semana</h3>
          <BarList
            items={ns.semanas.map(s => ({
              label: rotuloSemana(s.semana),
              value: s.erros_corrigidos,
              title: `Semana de ${rotuloSemana(s.semana)}`,
            }))}
          />
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <EtapaCard
          titulo="Aquisição"
          valor={aquisicao.alunos_previstos
            ? `${aquisicao.matriculados} de ${aquisicao.alunos_previstos}`
            : aquisicao.matriculados}
          detalhe={aquisicao.alunos_previstos
            ? `${pct(aquisicao.taxa_primeira_semana)} entraram na primeira semana.`
            : 'Informe quantos alunos a turma tem para ver a taxa de entrada.'}
          extra={textoOrigem}
          meta={aquisicao.alunos_previstos ? `Meta ${aquisicao.meta}%` : null}
          atingida={aquisicao.taxa_primeira_semana != null && aquisicao.taxa_primeira_semana >= aquisicao.meta}
        />
        <EtapaCard
          titulo="Ativação"
          valor={pct(ativacao.taxa)}
          detalhe={`${ativacao.ativados} de ${ativacao.matriculados} corrigiram o primeiro erro na primeira semana. ${ativacao.com_primeiro_envio} já enviaram algo.`}
          extra={textoSucesso(sucesso)}
          meta={`Meta ${ativacao.meta}%`}
          atingida={ativacao.taxa != null && ativacao.taxa >= ativacao.meta}
        />
        <EtapaCard
          titulo="Retenção"
          valor={pct(semana.taxa)}
          detalhe={`${semana.voltaram} de ${semana.base} abriram o app na semana de ${rotuloSemana(semana.semana)}. Pelo envio, ${pct(semana.taxa_por_envio)}.`}
          meta={`Meta ${retencao.meta}%`}
          atingida={semana.taxa != null && semana.taxa >= retencao.meta}
        />
      </div>

      <p className="text-xs text-cinza-texto">
        Hábito na semana de {rotuloSemana(semana.semana)}: {pct(semana.taxa_sem_prova_marcada)} voltaram sem prova marcada, {pct(semana.taxa_sem_aviso)} abriram sem aviso e {pct(semana.taxa_por_conta_propria)} enviaram em listas ou na trilha.
      </p>

      <AlunosEmRisco saude={saude} />

      <p className="text-xs text-cinza-texto">
        {media == null
          ? 'Proteção: ainda não há questão resolvida para medir.'
          : `Proteção: ${media} tentativas até acertar, em média, e ${pct(protecao.acerto_de_primeira)} de acerto de primeira.`}
      </p>
    </>
  )
}

export default function FunilDaTurma({ turmaId, recarga = 0 }) {
  const [estado, setEstado] = useState({ carregando: true, funil: null, erro: false })

  useEffect(() => {
    let ativo = true
    getTurmaFunil(turmaId)
      .then(({ data }) => { if (ativo) setEstado({ carregando: false, funil: data, erro: false }) })
      .catch(() => { if (ativo) setEstado({ carregando: false, funil: null, erro: true }) })
    return () => { ativo = false }
  }, [turmaId, recarga])

  return (
    <section className="space-y-4">
      <h2 className="text-sm font-semibold text-cinza-texto uppercase tracking-wide">Funil da turma</h2>
      {estado.carregando ? (
        <div className="flex justify-center py-8"><Spinner className="w-5 h-5 text-violeta" /></div>
      ) : estado.erro ? (
        <p className="text-sm text-erro">Não foi possível carregar o funil.</p>
      ) : estado.funil.aquisicao.matriculados === 0 ? (
        <p className="text-sm text-cinza-texto">O funil aparece quando os alunos entrarem pelo código da turma.</p>
      ) : (
        <Painel funil={estado.funil} />
      )}
    </section>
  )
}
