import { paraData } from './atividade'

// O backend manda o momento em ISO, e na tela só interessam o dia e o mês.
export function dataCurta(iso) {
  return paraData(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

// "hoje", "amanhã" ou "em N dias", contando dias de calendário no fuso do aluno.
export function prazoRelativo(iso, agora = new Date()) {
  const alvo = paraData(iso)
  const dia = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
  const dias = Math.round((dia(alvo) - dia(agora)) / 86400000)
  if (dias <= 0) return 'hoje'
  if (dias === 1) return 'amanhã'
  return `em ${dias} dias`
}
