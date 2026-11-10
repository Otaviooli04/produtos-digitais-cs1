import { Link, useOutletContext } from 'react-router-dom'

// O Layout já busca o nome da atividade para o menu e o passa pelo Outlet.
export default function LinkDaAtividade({ id }) {
  const atividade = useOutletContext()?.contexto?.atividade
  const nome = atividade && String(atividade.id) === String(id) ? atividade.nome : `Atividade #${id}`
  return (
    <Link to={`/exam/${id}`} className="hover:text-noite min-w-0 break-words">
      {nome}
    </Link>
  )
}
