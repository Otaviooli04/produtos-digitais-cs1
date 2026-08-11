// Rótulos curtos para as categorias de erro nos gráficos, onde o nome completo
// não cabe e acaba se sobrepondo. O nome completo continua no tooltip.
export const ERROR_SHORT_LABELS = {
  'Erro de Compilação': 'Compilação',
  'Saída Incorreta': 'Saída incorreta',
  'Acesso Indevido à Memória': 'Memória',
  'Acesso Fora dos Limites: Off-by-One': 'Off-by-one',
  'Loop Infinito: Controle de Fluxo': 'Loop infinito',
  'Timeout Anômalo': 'Timeout',
  'Tudo no Main': 'Tudo no main',
  'Recursão Faltando': 'Sem recursão',
  'Função Ausente': 'Função ausente',
  'Assinatura Incorreta': 'Assinatura',
  'Solução Sequencial: Sem Controle de Fluxo': 'Sem controle',
  'Erro Desconhecido': 'Desconhecido',
}

export const shortError = (cat) => ERROR_SHORT_LABELS[cat] ?? cat ?? 'Desconhecido'
