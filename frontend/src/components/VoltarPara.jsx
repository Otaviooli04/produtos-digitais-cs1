import { ArrowLeft } from 'lucide-react'
import { Link, useOutletContext } from 'react-router-dom'

/**
 * Volta para a tela de cima, não para a anterior do histórico: funciona igual
 * depois de recarregar ou de chegar por um link, e o rótulo diz para onde vai.
 * Mesmo visual do voltar das telas do aluno.
 */
export default function VoltarPara({ to, children, className = '' }) {
  return (
    <div className={className}>
      <Link
        to={to}
        className="inline-flex items-center gap-1 min-h-11 text-sm font-bold text-cinza-texto hover:text-noite"
      >
        <ArrowLeft className="w-4 h-4 shrink-0" aria-hidden="true" />
        <span className="break-words min-w-0">{children}</span>
      </Link>
    </div>
  )
}

// O Layout já busca o nome da atividade para o menu e o passa pelo Outlet.
export function VoltarParaAtividade({ id, className }) {
  const atividade = useOutletContext()?.contexto?.atividade
  const nome = atividade && String(atividade.id) === String(id) ? atividade.nome : 'Atividade'
  return <VoltarPara to={`/exam/${id}`} className={className}>{nome}</VoltarPara>
}
