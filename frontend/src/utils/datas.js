import { paraData } from './atividade'

// O backend manda o momento em ISO, e na tela só interessam o dia e o mês.
export function dataCurta(iso) {
  return paraData(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}
