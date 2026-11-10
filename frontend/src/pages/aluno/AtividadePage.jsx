import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { getAtividade } from '../../api/aluno'
import Badge from '../../components/Badge'
import Spinner from '../../components/Spinner'
import Card from '../../components/ui/Card'
import { categoriaColor, janelaTexto, modoLabel, situacaoInfo } from '../../utils/atividade'

function QuestaoLinha({ atividade, questao }) {
  const bloqueada = !atividade.aberta
  const semTentativas = questao.tentativas_restantes === 0 && !questao.resolvida

  return (
    <Card
      as={Link}
      to={`/aluno/atividades/${atividade.exam_id}/questoes/${questao.number}`}
      principal
      className="gap-0! transition-transform active:translate-x-0.5 active:translate-y-0.5"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="titulo-card">Questão {questao.number}</span>
            {questao.resolvida && <Badge color="green">Resolvida</Badge>}
            {!questao.resolvida && questao.ultima_categoria && (
              <Badge color={categoriaColor(questao.ultima_categoria)}>{questao.ultima_categoria}</Badge>
            )}
          </div>
          <p className="mt-1.5 text-sm text-cinza-texto line-clamp-2">{questao.statement}</p>
        </div>
        <span className="text-xs text-cinza-texto shrink-0">
          {questao.tentativas} tentativa{questao.tentativas === 1 ? '' : 's'}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-cinza-texto">
        {questao.testes_totais > 0 && (
          <span>melhor: {questao.melhor_testes_passados}/{questao.testes_totais} testes</span>
        )}
        {questao.tentativas_restantes != null && (
          <span>{questao.tentativas_restantes} tentativa(s) restante(s)</span>
        )}
        {questao.required_structures?.length > 0 && (
          <span>exige {questao.required_structures.join(', ')}</span>
        )}
        {(bloqueada || semTentativas) && <span className="text-aviso">sem envio disponível</span>}
      </div>
    </Card>
  )
}

export default function AtividadePage() {
  const { examId } = useParams()
  const [atividade, setAtividade] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getAtividade(examId)
      .then(({ data }) => setAtividade(data))
      .catch(err => setError(err.response?.data?.detail || 'Atividade não encontrada.'))
      .finally(() => setLoading(false))
  }, [examId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-violeta" />
      </div>
    )
  }

  if (!atividade) {
    return <p className="text-sm text-erro">{error}</p>
  }

  const situacao = situacaoInfo(atividade.situacao)
  const janela = janelaTexto(atividade)
  const detalhes = [
    janela,
    atividade.max_tentativas != null && `até ${atividade.max_tentativas} tentativas por questão`,
  ].filter(Boolean)

  return (
    <div className="space-y-6">
      <div>
        <Link to={`/aluno/turmas/${atividade.turma_id}`} className="inline-flex items-center gap-1 min-h-11 text-sm font-bold text-cinza-texto hover:text-noite">
          <ArrowLeft className="w-4 h-4 shrink-0" aria-hidden="true" />
          <span className="break-words">{atividade.turma_nome}</span>
        </Link>
        <div className="mt-1 flex flex-wrap items-center gap-2">
          <h1 className="titulo-pagina break-words">{atividade.titulo}</h1>
          <Badge color={atividade.modo === 'treino' ? 'purple' : 'gray'}>{modoLabel(atividade.modo)}</Badge>
          <Badge color={situacao.color}>{situacao.label}</Badge>
        </div>
        {detalhes.length > 0 && (
          <p className="mt-1 text-xs text-cinza-texto">{detalhes.join(' · ')}</p>
        )}
        <p className="mt-3 text-sm text-cinza-texto">
          {atividade.questoes_resolvidas} de {atividade.total_questoes} questões resolvidas
        </p>
      </div>

      {!atividade.aberta && (
        <div className="rounded-botao bg-aviso-fundo border-2 border-aviso px-4 py-3 text-sm text-aviso">
          {atividade.situacao === 'agendada'
            ? 'Esta atividade ainda não abriu. Você pode ler os enunciados, mas ainda não enviar.'
            : 'Esta atividade já encerrou. Você pode revisar suas tentativas, mas não enviar novas.'}
        </div>
      )}

      <div className="space-y-3">
        {atividade.questoes.map(q => (
          <QuestaoLinha key={q.id} atividade={atividade} questao={q} />
        ))}
      </div>
    </div>
  )
}
