import { Link } from 'react-router-dom'
import Badge from './Badge'
import { concluida, janelaTexto, situacaoInfo } from '../utils/atividade'

function ProgressoBarra({ resolvidas, total }) {
  const pct = total > 0 ? Math.round((resolvidas / total) * 100) : 0
  return (
    <div className="flex items-center gap-2 mt-3">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className="h-full rounded-full bg-purple-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-gray-400 w-24 text-right">{resolvidas}/{total} questões</span>
    </div>
  )
}

/** `mostrarTurma` só faz sentido fora da página da turma, onde ela é o contexto. */
export default function AtividadeCard({ atividade, mostrarTurma = false }) {
  const situacao = situacaoInfo(atividade.situacao)
  const janela = janelaTexto(atividade)
  const feita = concluida(atividade)

  return (
    <Link
      to={`/aluno/atividades/${atividade.exam_id}`}
      className="block bg-white rounded-xl border border-gray-200 p-5 hover:border-purple-300 transition-colors"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{atividade.titulo}</p>
          {mostrarTurma && (
            <p className="text-xs text-gray-400 mt-0.5">{atividade.turma_nome}</p>
          )}
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {feita
            ? <Badge color="green">Concluída</Badge>
            : <Badge color={situacao.color}>{situacao.label}</Badge>}
        </div>
      </div>

      <ProgressoBarra resolvidas={atividade.questoes_resolvidas} total={atividade.total_questoes} />

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
        <span>{atividade.tentativas} tentativa{atividade.tentativas === 1 ? '' : 's'}</span>
        {atividade.max_tentativas != null && (
          <span>máx. {atividade.max_tentativas} por questão</span>
        )}
        {janela && <span>{janela}</span>}
      </div>
    </Link>
  )
}
