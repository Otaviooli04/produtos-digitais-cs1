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

export const categoriaColor = (categoria) => {
  if (!categoria) return 'gray'
  if (categoria === 'Correto') return 'green'
  if (categoria.startsWith('Aviso')) return 'yellow'
  return 'red'
}
