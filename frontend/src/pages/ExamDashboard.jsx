import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ChevronRight, ClipboardList, Pencil, Plus, Trash2, TriangleAlert } from 'lucide-react'
import {
  getExam, getResults, getActiveJobs,
  deleteExam, updateExam, createQuestion, updateQuestion, deleteQuestion,
} from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import QuestionForm from '../components/QuestionForm'
import DisponibilidadeCard from '../components/DisponibilidadeCard'
import PublicacaoCard from '../components/PublicacaoCard'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import PainelDestaque from '../components/ui/PainelDestaque'
import Progresso from '../components/ui/Progresso'
import Tag from '../components/ui/Tag'
import { modoLabel } from '../utils/atividade'
import { avisarContextoMudou } from '../hooks/useContextoProfessor'

export default function ExamDashboard() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [exam, setExam] = useState(null)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [extractJob, setExtractJob] = useState(null)   // job de extração via Gemini
  const [statementQ, setStatementQ] = useState(null)   // questão no modal de enunciado
  const hadJob = useRef(false)

  // CRUD de prova / questão
  const [questionForm, setQuestionForm] = useState(null) // {mode:'add'|'edit', question}
  const [savingQ, setSavingQ] = useState(false)
  const [deleteQ, setDeleteQ] = useState(null)
  const [busy, setBusy] = useState(false)
  const [examDeleteOpen, setExamDeleteOpen] = useState(false)
  const [renameOpen, setRenameOpen] = useState(false)
  const [renameValue, setRenameValue] = useState('')

  const submitQuestion = async (data) => {
    setSavingQ(true)
    try {
      if (questionForm.mode === 'edit') {
        await updateQuestion(id, questionForm.question.number, data)
      } else {
        await createQuestion(id, data)
      }
      setQuestionForm(null)
      await loadExam()
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao salvar a questão.')
    } finally {
      setSavingQ(false)
    }
  }

  const confirmDeleteQuestion = async () => {
    setBusy(true)
    try {
      await deleteQuestion(id, deleteQ.number)
      setDeleteQ(null)
      await loadExam()
    } catch {
      setError('Erro ao excluir a questão.')
    } finally {
      setBusy(false)
    }
  }

  const confirmDeleteExam = async () => {
    setBusy(true)
    try {
      await deleteExam(id)
      navigate(exam?.turma_id ? `/turma/${exam.turma_id}?secao=atividades` : '/')
    } catch {
      setError('Erro ao excluir a atividade.')
      setBusy(false)
    }
  }

  const submitRename = async (e) => {
    e.preventDefault()
    if (!renameValue.trim()) return
    setBusy(true)
    try {
      await updateExam(id, { titulo: renameValue.trim() })
      avisarContextoMudou()
      setRenameOpen(false)
      await loadExam()
    } catch {
      setError('Erro ao renomear a atividade.')
    } finally {
      setBusy(false)
    }
  }

  const loadExam = () =>
    Promise.all([getExam(id), getResults(id).catch(() => null)])
      .then(([examRes, resultsRes]) => {
        setExam(examRes.data)
        if (resultsRes) setResults(resultsRes.data)
      })
      .catch(() => setError('Erro ao carregar a atividade.'))

  useEffect(() => {
    loadExam().finally(() => setLoading(false))
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  // Acompanha a extração de questões (Gemini) que roda em segundo plano: enquanto
  // houver um job ativo desta prova, exibe o progresso; ao concluir, recarrega.
  useEffect(() => {
    let alive = true
    const tick = async () => {
      try {
        const { data } = await getActiveJobs()
        if (!alive) return
        const job = data.find(j => j.exam_id === Number(id) && j.kind === 'exam_upload')
        setExtractJob(job || null)
        if (job) {
          hadJob.current = true
        } else if (hadJob.current) {
          hadJob.current = false
          loadExam()  // job terminou → questões/casos já persistidos
        }
      } catch { /* silencioso */ }
    }
    tick()
    const t = setInterval(tick, 2000)
    return () => { alive = false; clearInterval(t) }
  }, [id]) // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>
  if (error) return <p className="text-erro text-sm">{error}</p>

  const resultsByQuestion = {}
  results?.questions?.forEach(q => { resultsByQuestion[q.question_number] = q })

  // O que o aluno lê. Sem título definido, o nome do arquivo sem a extensão é um
  // ponto de partida melhor do que "prova1_2026.pdf".
  const nomeDaAtividade = exam.titulo || (exam.filename || '').replace(/\.[^.]+$/, '') || `Atividade ${id}`
  const tipo = modoLabel(exam.modo).toLowerCase()

  return (
    <div className="space-y-6">
      {exam.turma_id ? (
        <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto lg:hidden">
          <Link to="/" className="hover:text-noite">Turmas</Link>
          <ChevronRight className="w-4 h-4" aria-hidden="true" />
          <Link to={`/turma/${exam.turma_id}?secao=atividades`} className="hover:text-noite">{exam.turma_nome}</Link>
        </div>
      ) : null}

      <PainelDestaque>
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 space-y-2">
            <p className="text-sm text-white/80 break-words">{modoLabel(exam.modo)} #{id} · {exam.titulo || exam.filename}</p>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="titulo-pagina break-words">{nomeDaAtividade}</h1>
              <Badge color={exam.modo === 'treino' ? 'purple' : 'gray'}>{modoLabel(exam.modo)}</Badge>
              {!exam.publicada && <Badge color="yellow">rascunho</Badge>}
            </div>
          </div>
          <div className="flex shrink-0 gap-1">
            <button
              onClick={() => { setRenameValue(nomeDaAtividade); setRenameOpen(true) }}
              title="Nome da atividade"
              aria-label="Nome da atividade"
              className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-botao hover:bg-white/15 text-white"
            >
              <Pencil className="w-5 h-5" aria-hidden="true" />
            </button>
            <button
              onClick={() => setExamDeleteOpen(true)}
              title={`Excluir ${tipo}`}
              aria-label={`Excluir ${tipo}`}
              className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-botao hover:bg-white/15 text-white"
            >
              <Trash2 className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      </PainelDestaque>

      <PublicacaoCard
        exam={exam}
        onSave={async (dados) => { await updateExam(id, dados); await loadExam() }}
      />

      <DisponibilidadeCard
        exam={exam}
        onSave={async (dados) => { await updateExam(id, dados); await loadExam() }}
      />

      {extractJob && (
        <div className="rounded-botao border-2 border-violeta bg-lavanda px-5 py-4">
          <div className="flex items-center gap-3">
            <Spinner className="w-5 h-5 text-violeta" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-violeta">
                {extractJob.stage || 'Processando com Gemini…'}
              </p>
              <p className="text-xs text-violeta mt-0.5">
                Extração em segundo plano. Você pode continuar navegando; as questões aparecem ao concluir.
                {extractJob.total > 0 && ` (${extractJob.processed}/${extractJob.total} questões)`}
              </p>
            </div>
          </div>
          {extractJob.total > 0 && (
            <div className="mt-3">
              <Progresso valor={(extractJob.processed / extractJob.total) * 100} rotulo="Extração das questões" />
            </div>
          )}
        </div>
      )}

      {exam.questions.length === 0 && !extractJob && (
        <Card className="border-dashed border-noite/30! text-center p-10! items-center">
          <ClipboardList className="w-10 h-10 mx-auto mb-3 text-cinza-texto" aria-hidden="true" />
          <p className="text-sm text-cinza-texto">Nenhuma questão extraída.</p>
          <p className="text-xs text-cinza-texto mt-1">
            A extração pode ter falhado. Verifique a chave do Gemini e tente reenviar o arquivo.
          </p>
        </Card>
      )}

      <div className="flex items-center justify-between gap-3">
        {exam.questions.length > 0 && (
          <p className="text-sm text-cinza-texto">
            Valor total da {tipo}: <span className="font-bold text-noite">{exam.total_points ?? 0}</span>
          </p>
        )}
        <Botao variante="secundario" onClick={() => setQuestionForm({ mode: 'add', question: null })} className="ml-auto">
          <Plus className="w-4 h-4" aria-hidden="true" />
          Adicionar questão
        </Botao>
      </div>

      <div className="space-y-5">
        {exam.questions.map((q) => {
          const qr = resultsByQuestion[q.number]
          const passRate = qr && qr.total_submissions > 0
            ? Math.round((qr.passed_count / qr.total_submissions) * 100)
            : null

          return (
            <Card key={q.id} principal>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1.5">
                    <Tag>Q{q.number}</Tag>
                    <span className="text-xs text-cinza-texto">
                      Vale: <span className="font-bold text-noite">{q.points ?? 1}</span>
                    </span>
                    {q.required_structures.length > 0 && (
                      <span className="text-xs text-cinza-texto">
                        Exige: {q.required_structures.join(', ')}
                      </span>
                    )}
                    {q.forbidden_structures.length > 0 && (
                      <span className="text-xs text-erro">
                        Proíbe: {q.forbidden_structures.join(', ')}
                      </span>
                    )}
                    {q.required_functions?.length > 0 && (
                      <span className="text-xs text-cinza-texto">
                        Funções: {q.required_functions.map(f => f.name).join(', ')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-cinza-texto line-clamp-2 break-words">{q.statement}</p>
                  {q.statement && (
                    <button
                      onClick={() => setStatementQ(q)}
                      className="mt-1 min-h-11 text-xs font-bold text-violeta hover:text-violeta-escuro hover:underline"
                    >
                      Ver enunciado completo
                    </button>
                  )}
                  {q.warnings?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {q.warnings.map((w, i) => (
                        <p key={i} className="flex items-start gap-1.5 text-xs text-aviso bg-aviso-fundo border-2 border-aviso rounded-botao px-2 py-1">
                          <TriangleAlert className="w-3.5 h-3.5 mt-px shrink-0" aria-hidden="true" />
                          <span className="min-w-0 break-words">{w}</span>
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-4 shrink-0">
                  <div className="text-right">
                    <p className="text-xs text-cinza-texto">Test cases</p>
                    <p className="text-sm font-bold text-noite">{q.test_case_count}</p>
                  </div>
                  {qr && (
                    <div className="text-right">
                      <p className="text-xs text-cinza-texto">Submissões</p>
                      <p className="text-sm font-bold text-noite">{qr.total_submissions}</p>
                    </div>
                  )}
                  {passRate !== null && (
                    <Badge color={passRate >= 70 ? 'green' : passRate >= 40 ? 'yellow' : 'red'}>
                      {passRate}% corretos
                    </Badge>
                  )}
                </div>
              </div>

              <div className="flex flex-wrap gap-2 pt-3.5 border-t-2 border-noite/10">
                <Botao variante="secundario" to={`/exam/${id}/questions/${q.number}/testcases`} className="sm:min-h-9! px-3.5! text-[13px]!">
                  <Plus className="w-4 h-4" aria-hidden="true" />
                  Test cases
                </Botao>
                <Botao variante="secundario" to={`/exam/${id}/questions/${q.number}`} className="sm:min-h-9! px-3.5! text-[13px]!">
                  Respostas
                </Botao>
                <Botao variante="secundario" to={`/exam/${id}/questions/${q.number}?tab=cluster`} className="sm:min-h-9! px-3.5! text-[13px]!">
                  Grupos de dificuldade
                </Botao>
                <Botao
                  variante="secundario"
                  onClick={() => setQuestionForm({ mode: 'edit', question: q })}
                  className="sm:ml-auto sm:min-h-9! px-3.5! text-[13px]!"
                >
                  <Pencil className="w-4 h-4" aria-hidden="true" />
                  Editar
                </Botao>
                <Botao variante="perigo" onClick={() => setDeleteQ(q)} className="sm:min-h-9! px-3.5! text-[13px]!">
                  <Trash2 className="w-4 h-4" aria-hidden="true" />
                  Excluir
                </Botao>
              </div>
            </Card>
          )
        })}
      </div>

      <Modal
        open={!!statementQ}
        onClose={() => setStatementQ(null)}
        title={statementQ ? `Enunciado da questão ${statementQ.number}` : ''}
      >
        <p className="text-sm text-cinza-texto whitespace-pre-wrap leading-relaxed break-words">
          {statementQ?.statement}
        </p>
      </Modal>

      <Modal
        open={!!questionForm}
        onClose={() => setQuestionForm(null)}
        title={questionForm?.mode === 'edit' ? `Editar questão ${questionForm.question.number}` : 'Adicionar questão'}
      >
        {questionForm && (
          <QuestionForm
            initial={questionForm.question}
            isEdit={questionForm.mode === 'edit'}
            saving={savingQ}
            onSubmit={submitQuestion}
            onCancel={() => setQuestionForm(null)}
          />
        )}
      </Modal>

      <ConfirmDialog
        open={!!deleteQ}
        onClose={() => setDeleteQ(null)}
        onConfirm={confirmDeleteQuestion}
        loading={busy}
        title="Excluir questão"
        confirmLabel="Excluir questão"
        message={deleteQ
          ? `Excluir a questão ${deleteQ.number}? Test cases e submissões dela serão removidos permanentemente.`
          : ''}
      />

      <ConfirmDialog
        open={examDeleteOpen}
        onClose={() => setExamDeleteOpen(false)}
        onConfirm={confirmDeleteExam}
        loading={busy}
        title={`Excluir ${tipo}`}
        confirmLabel={`Excluir ${tipo}`}
        message={`Excluir a ${tipo} "${nomeDaAtividade}"? Todas as questões, test cases e submissões serão removidos permanentemente.`}
      />

      <Modal open={renameOpen} onClose={() => setRenameOpen(false)} title={`Renomear ${tipo}`}>
        <form onSubmit={submitRename} className="space-y-3">
          <input
            type="text" value={renameValue} onChange={e => setRenameValue(e.target.value)}
            className="campo"
          />
          <div className="flex justify-end gap-2">
            <Botao variante="secundario" onClick={() => setRenameOpen(false)}>
              Cancelar
            </Botao>
            <Botao type="submit" disabled={busy || !renameValue.trim()}>
              {busy && <Spinner className="w-4 h-4" />}
              Salvar
            </Botao>
          </div>
        </form>
      </Modal>
    </div>
  )
}
