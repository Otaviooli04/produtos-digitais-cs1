import { Link } from 'react-router-dom'
import Badge from './Badge'
import Card from './ui/Card'
import Progresso from './ui/Progresso'
import { corDaTaxa } from '../utils/coresGraficos'
import { concluida, janelaTexto, situacaoInfo } from '../utils/atividade'

function ProgressoBarra({ resolvidas, total }) {
  const pct = total > 0 ? Math.round((resolvidas / total) * 100) : 0
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 min-w-0">
        <Progresso valor={pct} rotulo="Questões resolvidas" cor={corDaTaxa(pct)} />
      </div>
      <span className="text-xs text-cinza-texto w-24 text-right">{resolvidas}/{total} questões</span>
    </div>
  )
}

/** `mostrarTurma` só faz sentido fora da página da turma, onde ela é o contexto. */
export default function AtividadeCard({ atividade, mostrarTurma = false }) {
  const situacao = situacaoInfo(atividade.situacao)
  const janela = janelaTexto(atividade)
  const feita = concluida(atividade)

  return (
    <Card
      as={Link}
      to={`/aluno/atividades/${atividade.exam_id}`}
      principal
      className="transition-transform active:translate-x-0.5 active:translate-y-0.5"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-bold text-noite break-words">{atividade.titulo}</p>
          {mostrarTurma && (
            <p className="text-xs text-cinza-texto mt-0.5">{atividade.turma_nome}</p>
          )}
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {feita
            ? <Badge color="green">Concluída</Badge>
            : <Badge color={situacao.color}>{situacao.label}</Badge>}
        </div>
      </div>

      <ProgressoBarra resolvidas={atividade.questoes_resolvidas} total={atividade.total_questoes} />

      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-cinza-texto">
        <span>{atividade.tentativas} tentativa{atividade.tentativas === 1 ? '' : 's'}</span>
        {atividade.max_tentativas != null && (
          <span>máx. {atividade.max_tentativas} por questão</span>
        )}
        {janela && <span>{janela}</span>}
      </div>
    </Card>
  )
}
