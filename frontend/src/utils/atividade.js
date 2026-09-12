// Rótulos das atividades no lado do aluno. Modo diz o que a atividade é,
// situação diz se ela está aberta agora.
export const MODO_LABEL = {
  treino: 'Treino',
  prova: 'Prova',
}

export const SITUACAO = {
  aberta: { label: 'Aberta', color: 'green' },
  agendada: { label: 'Ainda não abriu', color: 'yellow' },
  encerrada: { label: 'Encerrada', color: 'gray' },
}

export const modoLabel = (modo) => MODO_LABEL[modo] ?? 'Prova'

export const situacaoInfo = (situacao) => SITUACAO[situacao] ?? SITUACAO.aberta

// O backend guarda datas em UTC sem fuso na string. Sem o 'Z' o JS interpretaria
// como hora local e o horário apareceria deslocado.
const COM_FUSO = /(Z|[+-]\d{2}:?\d{2})$/

export const paraData = (iso) => new Date(COM_FUSO.test(iso) ? iso : `${iso}Z`)

export const formatarData = (iso) => {
  if (!iso) return null
  return paraData(iso).toLocaleString('pt-BR', {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

/** "há 3 minutos", "há 2 horas". Serve para dizer quando o grupo foi formado. */
export const formatRelativo = (iso) => {
  if (!iso) return ''
  const segundos = Math.round((Date.now() - paraData(iso).getTime()) / 1000)
  if (segundos < 60) return 'agora há pouco'
  const minutos = Math.round(segundos / 60)
  if (minutos < 60) return `há ${minutos} minuto${minutos !== 1 ? 's' : ''}`
  const horas = Math.round(minutos / 60)
  if (horas < 24) return `há ${horas} hora${horas !== 1 ? 's' : ''}`
  const dias = Math.round(horas / 24)
  if (dias < 30) return `há ${dias} dia${dias !== 1 ? 's' : ''}`
  return `em ${formatarData(iso)}`
}

/** ISO (UTC) → valor de um <input type="datetime-local"> na hora local. */
export const isoParaInputLocal = (iso) => {
  if (!iso) return ''
  const d = paraData(iso)
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
}

/** Valor de <input type="datetime-local"> (hora local) → ISO em UTC. */
export const inputLocalParaIso = (valor) => {
  if (!valor) return null
  return new Date(valor).toISOString().slice(0, 19)
}

export const janelaTexto = (atividade) => {
  const abre = formatarData(atividade.abre_em)
  const fecha = formatarData(atividade.fecha_em)
  if (abre && fecha) return `${abre} até ${fecha}`
  if (fecha) return `até ${fecha}`
  if (abre) return `a partir de ${abre}`
  return null
}

// Uma atividade sai da frente quando o aluno resolveu todas as questões dela.
export const concluida = (atividade) =>
  atividade.total_questoes > 0
  && atividade.questoes_resolvidas === atividade.total_questoes

const ORDEM_SITUACAO = { aberta: 0, agendada: 1, encerrada: 2 }

/** O que exige ação primeiro: aberta, agendada, encerrada, concluídas ao fim. */
export const ordenarAtividades = (atividades) =>
  [...atividades].sort((a, b) => {
    const feitaA = concluida(a) ? 1 : 0
    const feitaB = concluida(b) ? 1 : 0
    if (feitaA !== feitaB) return feitaA - feitaB

    const situacaoA = ORDEM_SITUACAO[a.situacao] ?? 0
    const situacaoB = ORDEM_SITUACAO[b.situacao] ?? 0
    if (situacaoA !== situacaoB) return situacaoA - situacaoB

    return a.titulo.localeCompare(b.titulo, 'pt-BR')
  })

export const categoriaColor = (categoria) => {
  if (!categoria) return 'gray'
  if (categoria === 'Correto') return 'green'
  if (categoria.startsWith('Aviso')) return 'yellow'
  return 'red'
}
