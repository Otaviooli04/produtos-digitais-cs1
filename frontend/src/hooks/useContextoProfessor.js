import { useEffect, useState } from 'react'
import { useMatch } from 'react-router-dom'
import { getExam, getTurma } from '../api/exam'

const CONTEXTO_MUDOU = 'centralized:contexto-mudou'
const VAZIO = { turma: null, atividade: null }

export function avisarContextoMudou() {
  window.dispatchEvent(new Event(CONTEXTO_MUDOU))
}

function nomeDaAtividade(exam, id) {
  return exam.titulo || (exam.filename || '').replace(/\.[^.]+$/, '') || `Atividade ${id}`
}

// A página da turma ou da atividade também busca esses dados. A busca duplicada
// é aceita para o menu não depender de cada página.
export default function useContextoProfessor() {
  const naTurma = useMatch('/turma/:turmaId/*')
  const naAtividade = useMatch('/exam/:id/*')
  const turmaId = naTurma?.params.turmaId ?? null
  const examId = naAtividade?.params.id ?? null
  const chave = `${turmaId}|${examId}`
  const [dados, setDados] = useState({ chave: null, ...VAZIO })
  const [versao, setVersao] = useState(0)

  useEffect(() => {
    const aoMudar = () => setVersao(v => v + 1)
    window.addEventListener(CONTEXTO_MUDOU, aoMudar)
    return () => window.removeEventListener(CONTEXTO_MUDOU, aoMudar)
  }, [])

  useEffect(() => {
    if (!turmaId && !examId) return undefined
    let ativo = true
    const busca = examId
      ? getExam(examId).then(({ data }) => ({
          turma: data.turma_id ? { id: data.turma_id, nome: data.turma_nome } : null,
          atividade: { id: examId, nome: nomeDaAtividade(data, examId) },
        }))
      : getTurma(turmaId).then(({ data }) => ({
          turma: { id: turmaId, nome: data.nome },
          atividade: null,
        }))
    busca
      .then(r => { if (ativo) setDados({ chave, ...r }) })
      .catch(() => { if (ativo) setDados({ chave, ...VAZIO }) })
    return () => { ativo = false }
  }, [chave, turmaId, examId, versao])

  return dados.chave === chave ? dados : VAZIO
}
