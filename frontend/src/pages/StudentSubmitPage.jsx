import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getExam, submitCode } from '../api/exam'
import Spinner from '../components/Spinner'
import Badge from '../components/Badge'
import FunctionCheckCard from '../components/FunctionCheckCard'
import Logo from '../components/Logo'

function formatRequiredFunction(fn) {
  const tags = []
  if (fn.requires_recursion) tags.push('recursiva')
  if (fn.requires_pointer_param) tags.push('ponteiro')
  const params = fn.param_count != null ? `(${fn.param_count} param.)` : ''
  const suffix = tags.length ? ` [${tags.join(', ')}]` : ''
  return `${fn.name}${params}${suffix}`
}

export default function StudentSubmitPage() {
  const { examId } = useParams()
  const [exam, setExam] = useState(null)
  const [loading, setLoading] = useState(true)
  const [matricula, setMatricula] = useState('')
  const [selectedQuestion, setSelectedQuestion] = useState('')
  const [code, setCode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [submitted, setSubmitted] = useState(false)

  useEffect(() => {
    getExam(examId)
      .then(({ data }) => {
        setExam(data)
        if (data.questions.length > 0) setSelectedQuestion(data.questions[0].number)
      })
      .catch(() => setError('Prova não encontrada.'))
      .finally(() => setLoading(false))
  }, [examId])

  const handleSubmit = async () => {
    if (!matricula.trim()) { setError('Informe seu número de matrícula antes de enviar.'); return }
    if (!code.trim()) { setError('Escreva o código antes de enviar.'); return }
    setError('')
    setSubmitting(true)
    setResult(null)
    try {
      const { data } = await submitCode(examId, selectedQuestion, code, matricula.trim())
      setResult(data)
      setSubmitted(true)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao enviar. Tente novamente.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleNewSubmission = () => {
    setResult(null)
    setSubmitted(false)
    setCode('')
    setError('')
  }

  const currentQuestion = exam?.questions.find(q => q.number === selectedQuestion)

  const diagColor = (cat) => {
    if (!cat) return 'gray'
    if (cat === 'Correto') return 'green'
    if (cat.startsWith('Aviso')) return 'yellow'
    return 'red'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  if (!exam) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-sm text-red-600">{error || 'Prova não encontrada.'}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-2xl mx-auto px-6 h-14 flex items-center gap-3">
          <Logo className="w-7 h-7" />
          <div>
            <span className="text-sm font-semibold text-gray-900">{exam.filename}</span>
            {exam.turma_nome && (
              <span className="ml-2 text-xs text-gray-400">{exam.turma_nome}</span>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-6 py-8">
        {!submitted ? (
          <div className="space-y-4">
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Número de matrícula</label>
              <input
                type="text"
                value={matricula}
                onChange={e => setMatricula(e.target.value)}
                placeholder="Ex: 12345678"
                className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Questão</label>
              <div className="flex gap-2 flex-wrap mb-4">
                {exam.questions.map(q => (
                  <button
                    key={q.id}
                    onClick={() => { setSelectedQuestion(q.number); setResult(null) }}
                    className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                      selectedQuestion === q.number
                        ? 'bg-purple-600 text-white border-purple-600'
                        : 'border-gray-200 text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    Q{q.number}
                  </button>
                ))}
              </div>

              {currentQuestion && (
                <div className="rounded-lg bg-gray-50 border border-gray-100 px-4 py-3 mb-4">
                  <p className="text-sm text-gray-700 leading-relaxed">{currentQuestion.statement}</p>
                  {currentQuestion.required_structures.length > 0 && (
                    <p className="mt-2 text-xs text-gray-400">
                      Estruturas obrigatórias: <span className="text-purple-600">{currentQuestion.required_structures.join(', ')}</span>
                    </p>
                  )}
                  {currentQuestion.forbidden_structures.length > 0 && (
                    <p className="mt-1 text-xs text-red-400">
                      Proibido: {currentQuestion.forbidden_structures.join(', ')}
                    </p>
                  )}
                  {currentQuestion.required_functions?.length > 0 && (
                    <p className="mt-1 text-xs text-gray-400">
                      Funções exigidas: <span className="text-purple-600">{currentQuestion.required_functions.map(formatRequiredFunction).join(', ')}</span>
                    </p>
                  )}
                </div>
              )}

              <label className="block text-xs font-medium text-gray-500 mb-1.5">Código C</label>
              <textarea
                rows={16}
                value={code}
                onChange={e => setCode(e.target.value)}
                placeholder={"#include <stdio.h>\n\nint main() {\n    \n    return 0;\n}"}
                spellCheck={false}
                className="w-full text-sm font-mono rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none bg-gray-50"
              />
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              onClick={handleSubmit}
              disabled={submitting || !code.trim() || !matricula.trim()}
              className="w-full inline-flex items-center justify-center gap-2 text-sm px-4 py-3 rounded-xl bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors font-medium"
            >
              {submitting && <Spinner className="w-4 h-4" />}
              {submitting ? 'Enviando…' : 'Enviar resposta'}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="flex items-center gap-3 mb-3">
                <Badge color={diagColor(result.diagnosis?.error_category)}>
                  {result.diagnosis?.error_category}
                </Badge>
                <span className="text-xs text-gray-400">Questão {selectedQuestion} ({matricula})</span>
              </div>
              <p className="text-sm text-gray-700">{result.diagnosis?.pedagogical_diagnosis}</p>
              {result.diagnosis?.actionable_feedback && (
                <div className="mt-3 rounded-lg bg-blue-50 border border-blue-100 px-4 py-2.5">
                  <p className="text-xs text-blue-700">{result.diagnosis.actionable_feedback}</p>
                </div>
              )}
            </div>

            {result.function_check && !result.function_check.compliant && (
              <FunctionCheckCard check={result.function_check} />
            )}

            {result.compile_error && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Erro de compilação</h3>
                <pre className="text-xs font-mono bg-gray-900 rounded-lg p-3 overflow-x-auto text-red-400 whitespace-pre-wrap">{result.compile_error}</pre>
              </div>
            )}

            {result.warnings && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Avisos do compilador</h3>
                <pre className="text-xs font-mono bg-gray-900 rounded-lg p-3 overflow-x-auto text-yellow-400 whitespace-pre-wrap">{result.warnings}</pre>
              </div>
            )}

            {result.test_results?.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Testes: {result.test_results.filter(t => t.passed).length}/{result.test_results.length} passaram
                </h3>
                <div className="space-y-2">
                  {result.test_results.map((tr, i) => (
                    <div key={i} className={`rounded-lg border px-4 py-3 ${tr.passed ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className={`text-xs font-semibold ${tr.passed ? 'text-green-700' : 'text-red-700'}`}>
                          {tr.passed ? '✓ Correto' : '✗ Incorreto'}
                        </span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                        <div><span className="text-gray-400">entrada: </span><span className="text-gray-700">{tr.input || '(vazia)'}</span></div>
                        <div><span className="text-gray-400">esperado: </span><span className="text-gray-700">{tr.expected_output}</span></div>
                        <div><span className="text-gray-400">obtido: </span><span className={tr.passed ? 'text-green-700' : 'text-red-700'}>{tr.actual_output}</span></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleNewSubmission}
                className="flex-1 text-sm px-4 py-2.5 rounded-xl border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Tentar novamente
              </button>
              <button
                onClick={() => { handleNewSubmission(); setSelectedQuestion(exam.questions.find(q => q.number !== selectedQuestion)?.number || selectedQuestion) }}
                className="flex-1 text-sm px-4 py-2.5 rounded-xl bg-purple-600 text-white hover:bg-purple-700 transition-colors"
              >
                Outra questão
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
