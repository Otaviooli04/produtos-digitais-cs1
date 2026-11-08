import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getExam, submitCode } from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import FunctionCheckCard from '../components/FunctionCheckCard'
import CodeTextarea from '../components/CodeTextarea'

export default function SubmitPage() {
  const { id } = useParams()
  const [exam, setExam] = useState(null)
  const [selectedQuestion, setSelectedQuestion] = useState('')
  const [code, setCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getExam(id).then(({ data }) => {
      setExam(data)
      if (data.questions.length > 0) setSelectedQuestion(data.questions[0].number)
    })
  }, [id])

  const submit = async () => {
    if (!code.trim() || !selectedQuestion) return
    setSubmitting(true)
    setResult(null)
    setError('')
    try {
      const { data } = await submitCode(id, selectedQuestion, code, null, true)
      setResult(data)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao avaliar o código.')
    } finally {
      setSubmitting(false)
    }
  }

  if (!exam) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>

  const diagColor = (cat) => {
    if (!cat) return 'gray'
    if (cat === 'Correto') return 'green'
    if (cat.startsWith('Aviso')) return 'yellow'
    return 'red'
  }

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-2 text-sm text-cinza-texto mb-6">
        <Link to={`/exam/${id}`} className="hover:text-cinza-texto">Atividade #{id}</Link>
        <span>›</span>
        <span className="text-cinza-texto">Testar submissão</span>
      </div>

      <h1 className="text-xl font-semibold text-noite mb-6">Testar submissão</h1>

      <div className="bg-white rounded-xl border border-noite/20 p-5 mb-4">
        <div className="mb-4">
          <label className="block text-xs font-medium text-cinza-texto mb-1.5">Questão</label>
          <select
            value={selectedQuestion}
            onChange={e => setSelectedQuestion(e.target.value)}
            className="text-sm rounded-lg border border-noite/20 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violeta focus:border-transparent"
          >
            {exam.questions.map(q => (
              <option key={q.id} value={q.number}>Questão {q.number}</option>
            ))}
          </select>
        </div>

        {selectedQuestion && (
          <div className="mb-4 rounded-lg bg-lavanda border border-noite/10 px-4 py-3">
            <p className="text-xs text-cinza-texto line-clamp-3">
              {exam.questions.find(q => q.number === selectedQuestion)?.statement}
            </p>
          </div>
        )}

        <div>
          <label className="block text-xs font-medium text-cinza-texto mb-1.5">Código C</label>
          <CodeTextarea
            rows={14}
            value={code}
            onChange={e => setCode(e.target.value)}
            placeholder="#include <stdio.h>&#10;&#10;int main() {&#10;    return 0;&#10;}"
            className="w-full text-sm font-mono rounded-lg border border-noite/20 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-violeta focus:border-transparent resize-none"
          />
        </div>

        <div className="flex justify-end mt-3">
          <button
            onClick={submit}
            disabled={submitting || !code.trim()}
            className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-violeta text-white hover:bg-violeta-escuro disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {submitting && <Spinner className="w-4 h-4" />}
            Avaliar
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-erro-fundo border border-erro/30 px-4 py-3 text-sm text-erro mb-4">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-3">
          <div className="bg-white rounded-xl border border-noite/20 p-5">
            <div className="flex items-start gap-3">
              <Badge color={diagColor(result.diagnosis?.error_category)}>
                {result.diagnosis?.error_category}
              </Badge>
            </div>
            <p className="mt-3 text-sm text-cinza-texto">{result.diagnosis?.pedagogical_diagnosis}</p>
            {result.diagnosis?.actionable_feedback && (
              <div className="mt-2 rounded-lg bg-lavanda border border-violeta/15 px-4 py-2.5">
                <p className="text-xs text-violeta">{result.diagnosis.actionable_feedback}</p>
              </div>
            )}
          </div>

          {result.function_check && !result.function_check.compliant && (
            <FunctionCheckCard check={result.function_check} />
          )}

          {result.compile_error && (
            <div className="bg-white rounded-xl border border-noite/20 p-5">
              <h3 className="text-sm font-medium text-cinza-texto mb-2">Erro de compilação</h3>
              <pre className="text-xs font-mono bg-lavanda rounded-lg p-3 overflow-x-auto text-erro whitespace-pre-wrap">{result.compile_error}</pre>
            </div>
          )}

          {result.warnings && (
            <div className="bg-white rounded-xl border border-noite/20 p-5">
              <h3 className="text-sm font-medium text-cinza-texto mb-2">Avisos</h3>
              <pre className="text-xs font-mono bg-aviso-fundo rounded-lg p-3 overflow-x-auto text-aviso whitespace-pre-wrap">{result.warnings}</pre>
            </div>
          )}

          {result.test_results?.length > 0 && (
            <div className="bg-white rounded-xl border border-noite/20 p-5">
              <h3 className="text-sm font-medium text-cinza-texto mb-3">Resultados dos testes</h3>
              <div className="space-y-2">
                {result.test_results.map((tr, i) => (
                  <div key={i} className={`rounded-lg border px-4 py-3 ${tr.passed ? 'bg-sucesso-fundo border-sucesso/30' : 'bg-erro-fundo border-erro/30'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-semibold ${tr.passed ? 'text-sucesso' : 'text-erro'}`}>
                        {tr.passed ? '✓ Passou' : '✗ Falhou'}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                      <div><span className="text-cinza-texto">entrada:</span> <span className="text-cinza-texto">{tr.input || '(vazia)'}</span></div>
                      <div><span className="text-cinza-texto">esperado:</span> <span className="text-cinza-texto">{tr.expected_output}</span></div>
                      <div><span className="text-cinza-texto">obtido:</span> <span className={tr.passed ? 'text-sucesso' : 'text-erro'}>{tr.actual_output}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
