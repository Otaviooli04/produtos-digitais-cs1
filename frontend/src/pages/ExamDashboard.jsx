import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import {
  getExam, getResults, getActiveJobs,
  deleteExam, updateExam, createQuestion, updateQuestion, deleteQuestion,
} from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import QuestionForm from '../components/QuestionForm'
import Logo from '../components/Logo'

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
      navigate(exam?.turma_id ? `/turma/${exam.turma_id}` : '/')
    } catch {
      setError('Erro ao excluir a prova.')
      setBusy(false)
    }
  }

  const submitRename = async (e) => {
    e.preventDefault()
    if (!renameValue.trim()) return
    setBusy(true)
    try {
      await updateExam(id, { filename: renameValue.trim() })
      setRenameOpen(false)
      await loadExam()
    } catch {
      setError('Erro ao renomear a prova.')
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
      .catch(() => setError('Erro ao carregar a prova.'))

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

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>
  if (error) return <p className="text-red-600 text-sm">{error}</p>

  const resultsByQuestion = {}
  results?.questions?.forEach(q => { resultsByQuestion[q.question_number] = q })

  return (
    <div>
      {exam.turma_id ? (
        <div className="flex items-center gap-2 text-sm text-gray-400 mb-2">
          <Link to="/" className="hover:text-gray-600">Turmas</Link>
          <span>›</span>
          <Link to={`/turma/${exam.turma_id}`} className="hover:text-gray-600">{exam.turma_nome}</Link>
          <span>›</span>
          <span className="text-gray-600">{exam.filename}</span>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-3 mb-6">
        <div className="min-w-0">
          <p className="text-xs text-gray-400 mb-0.5">Prova #{id}</p>
          <h1 className="text-xl font-semibold text-gray-900 truncate">{exam.filename}</h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/exam/${id}/students`}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
            </svg>
            Alunos
          </Link>
          <Link
            to={`/exam/${id}/submit`}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 9.75L16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0020.25 18V7.5l-4.5-4.5h-9.75A2.25 2.25 0 003.75 5.25v12.75A2.25 2.25 0 006 20.25z" />
            </svg>
            Testar submissão
          </Link>
          <Link
            to={`/exam/${id}/bulk-submit`}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 8.25H7.5a2.25 2.25 0 00-2.25 2.25v9a2.25 2.25 0 002.25 2.25h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25H15M9 12l3 3m0 0l3-3m-3 3V2.25" />
            </svg>
            Submissões em lote
          </Link>
          <Link
            to={`/exam/${id}/results`}
            className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
            Resultados
          </Link>
          <button
            onClick={() => { setRenameValue(exam.filename); setRenameOpen(true) }}
            title="Renomear prova"
            aria-label="Renomear prova"
            className="inline-flex items-center justify-center p-2 rounded-lg border border-gray-200 text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
            </svg>
          </button>
          <button
            onClick={() => setExamDeleteOpen(true)}
            title="Excluir prova"
            aria-label="Excluir prova"
            className="inline-flex items-center justify-center p-2 rounded-lg border border-red-200 text-red-500 hover:text-red-600 hover:bg-red-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            </svg>
          </button>
        </div>
      </div>

      {extractJob && (
        <div className="mb-5 rounded-xl border border-purple-200 bg-purple-50 px-5 py-4">
          <div className="flex items-center gap-3">
            <Spinner className="w-5 h-5 text-purple-600" />
            <div className="flex-1">
              <p className="text-sm font-medium text-purple-800">
                {extractJob.stage || 'Processando com Gemini…'}
              </p>
              <p className="text-xs text-purple-600 mt-0.5">
                Extração em segundo plano. Você pode continuar navegando; as questões aparecem ao concluir.
                {extractJob.total > 0 && ` (${extractJob.processed}/${extractJob.total} questões)`}
              </p>
            </div>
          </div>
          {extractJob.total > 0 && (
            <div className="mt-3 w-full bg-purple-100 rounded-full h-1.5">
              <div
                className="h-1.5 rounded-full bg-purple-500 transition-all"
                style={{ width: `${Math.round((extractJob.processed / extractJob.total) * 100)}%` }}
              />
            </div>
          )}
        </div>
      )}

      {exam.questions.length === 0 && !extractJob && (
        <div className="rounded-xl border border-gray-200 bg-white px-5 py-10 text-center">
          <Logo className="w-10 h-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm text-gray-500">Nenhuma questão extraída.</p>
          <p className="text-xs text-gray-400 mt-1">
            A extração pode ter falhado. Verifique a chave do Gemini e tente reenviar a prova.
          </p>
        </div>
      )}

      <div className="flex items-center justify-between mb-3">
        {exam.questions.length > 0 && (
          <p className="text-sm text-gray-500">
            Valor total da prova: <span className="font-medium text-gray-700">{exam.total_points ?? 0}</span>
          </p>
        )}
        <button
          onClick={() => setQuestionForm({ mode: 'add', question: null })}
          className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors ml-auto"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Adicionar questão
        </button>
      </div>

      <div className="space-y-3">
        {exam.questions.map((q) => {
          const qr = resultsByQuestion[q.number]
          const passRate = qr && qr.total_submissions > 0
            ? Math.round((qr.passed_count / qr.total_submissions) * 100)
            : null

          return (
            <div key={q.id} className="bg-white rounded-xl border border-gray-200 p-5 hover:border-gray-300 hover:shadow-sm transition-all">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs font-semibold text-purple-600 bg-purple-50 px-2 py-0.5 rounded-md">
                      Q{q.number}
                    </span>
                    <span className="text-xs text-gray-500">
                      Vale: <span className="font-medium text-gray-700">{q.points ?? 1}</span>
                    </span>
                    {q.required_structures.length > 0 && (
                      <span className="text-xs text-gray-400">
                        Exige: {q.required_structures.join(', ')}
                      </span>
                    )}
                    {q.forbidden_structures.length > 0 && (
                      <span className="text-xs text-red-400">
                        Proíbe: {q.forbidden_structures.join(', ')}
                      </span>
                    )}
                    {q.required_functions?.length > 0 && (
                      <span className="text-xs text-gray-400">
                        Funções: {q.required_functions.map(f => f.name).join(', ')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">{q.statement}</p>
                  {q.statement && (
                    <button
                      onClick={() => setStatementQ(q)}
                      className="mt-1 text-xs text-purple-600 hover:text-purple-700 hover:underline"
                    >
                      Ver enunciado completo
                    </button>
                  )}
                  {q.warnings?.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {q.warnings.map((w, i) => (
                        <p key={i} className="flex items-start gap-1.5 text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-2 py-1">
                          <svg className="w-3.5 h-3.5 mt-px shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                          </svg>
                          {w}
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex items-center gap-4 shrink-0">
                  <div className="text-right">
                    <p className="text-xs text-gray-400">Test cases</p>
                    <p className="text-sm font-semibold text-gray-900">{q.test_case_count}</p>
                  </div>
                  {qr && (
                    <div className="text-right">
                      <p className="text-xs text-gray-400">Submissões</p>
                      <p className="text-sm font-semibold text-gray-900">{qr.total_submissions}</p>
                    </div>
                  )}
                  {passRate !== null && (
                    <Badge color={passRate >= 70 ? 'green' : passRate >= 40 ? 'yellow' : 'red'}>
                      {passRate}% corretos
                    </Badge>
                  )}
                </div>
              </div>

              <div className="flex gap-2 mt-4 pt-4 border-t border-gray-100">
                <Link
                  to={`/exam/${id}/questions/${q.number}/testcases`}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  + Test cases
                </Link>
                <Link
                  to={`/exam/${id}/questions/${q.number}`}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  Respostas
                </Link>
                <Link
                  to={`/exam/${id}/questions/${q.number}?tab=cluster`}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  Grupos de dificuldade
                </Link>
                <button
                  onClick={() => setQuestionForm({ mode: 'edit', question: q })}
                  className="ml-auto text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  Editar
                </button>
                <button
                  onClick={() => setDeleteQ(q)}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
                >
                  Excluir
                </button>
              </div>
            </div>
          )
        })}
      </div>

      <Modal
        open={!!statementQ}
        onClose={() => setStatementQ(null)}
        title={statementQ ? `Enunciado da questão ${statementQ.number}` : ''}
      >
        <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
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
        title="Excluir prova"
        confirmLabel="Excluir prova"
        message={`Excluir a prova "${exam.filename}"? Todas as questões, test cases e submissões serão removidos permanentemente.`}
      />

      <Modal open={renameOpen} onClose={() => setRenameOpen(false)} title="Renomear prova">
        <form onSubmit={submitRename} className="space-y-3">
          <input
            type="text" value={renameValue} onChange={e => setRenameValue(e.target.value)}
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => setRenameOpen(false)}
              className="text-sm px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={busy || !renameValue.trim()}
              className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors">
              {busy && <Spinner className="w-4 h-4" />}
              Salvar
            </button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
