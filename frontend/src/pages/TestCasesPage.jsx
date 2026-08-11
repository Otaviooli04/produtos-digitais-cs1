import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getExam, getTestCases, addTestCases, updateTestCase, deleteTestCase } from '../api/exam'
import Spinner from '../components/Spinner'

export default function TestCasesPage() {
  const { id, num } = useParams()
  const [question, setQuestion] = useState(null)
  const [saved, setSaved] = useState([])
  const [loadingSaved, setLoadingSaved] = useState(true)
  const [pending, setPending] = useState([])
  const [input, setInput] = useState('')
  const [expected, setExpected] = useState('')
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [error, setError] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editInput, setEditInput] = useState('')
  const [editExpected, setEditExpected] = useState('')
  const [deletingId, setDeletingId] = useState(null)

  const loadData = () => {
    setLoadingSaved(true)
    Promise.all([
      getExam(id),
      getTestCases(id, num),
    ]).then(([examRes, tcRes]) => {
      setQuestion(examRes.data.questions.find(q => q.number === num))
      setSaved(tcRes.data)
    }).finally(() => setLoadingSaved(false))
  }

  useEffect(() => { loadData() }, [id, num]) // eslint-disable-line react-hooks/exhaustive-deps

  const addLocal = () => {
    if (!input.trim() || !expected.trim()) return
    setPending(prev => [...prev, { input: input.trim(), expected_output: expected.trim() }])
    setInput('')
    setExpected('')
  }

  const removePending = (i) => setPending(prev => prev.filter((_, idx) => idx !== i))

  const save = async () => {
    if (pending.length === 0) return
    setSaving(true)
    setError('')
    try {
      await addTestCases(id, num, pending)
      setPending([])
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 3000)
      loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao salvar.')
    } finally {
      setSaving(false)
    }
  }

  const startEdit = (tc) => {
    setEditingId(tc.id)
    setEditInput(tc.input)
    setEditExpected(tc.expected_output)
  }

  const cancelEdit = () => setEditingId(null)

  const confirmEdit = async (tc) => {
    try {
      await updateTestCase(id, num, tc.id, { input: editInput, expected_output: editExpected })
      setEditingId(null)
      loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao editar.')
    }
  }

  const confirmDelete = async (tcId) => {
    setDeletingId(tcId)
    try {
      await deleteTestCase(id, num, tcId)
      loadData()
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao excluir.')
    } finally {
      setDeletingId(null)
    }
  }

  if (!question) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-purple-600" /></div>

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <span>Questão {num}</span>
        <span>›</span>
        <span className="text-gray-600">Test cases</span>
      </div>

      <h1 className="text-xl font-semibold text-gray-900 mb-1">Test cases</h1>
      <p className="text-sm text-gray-500 line-clamp-2 mb-6">{question.statement}</p>

      {/* Cadastrados */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <h2 className="text-sm font-medium text-gray-700">Cadastrados</h2>
          {!loadingSaved && (
            <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
              {saved.length}
            </span>
          )}
        </div>

        {loadingSaved ? (
          <div className="flex justify-center py-6"><Spinner className="w-5 h-5 text-purple-600" /></div>
        ) : saved.length === 0 ? (
          <p className="text-sm text-gray-400 py-4 text-center border border-dashed border-gray-200 rounded-xl">
            Nenhum test case cadastrado ainda.
          </p>
        ) : (
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
            {saved.map((tc, i) => (
              <div key={tc.id} className="px-5 py-3">
                {editingId === tc.id ? (
                  <div>
                    <div className="grid grid-cols-2 gap-3 mb-2">
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Entrada</label>
                        <textarea
                          rows={3}
                          value={editInput}
                          onChange={e => setEditInput(e.target.value)}
                          className="w-full text-sm font-mono rounded-lg border border-purple-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-400 mb-1">Saída esperada</label>
                        <textarea
                          rows={3}
                          value={editExpected}
                          onChange={e => setEditExpected(e.target.value)}
                          className="w-full text-sm font-mono rounded-lg border border-purple-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => confirmEdit(tc)}
                        className="text-xs px-2.5 py-1.5 rounded-md bg-purple-600 text-white hover:bg-purple-700 transition-colors"
                      >
                        Salvar
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-400 shrink-0 w-5">#{i + 1}</span>
                    <div className="flex-1 grid grid-cols-2 gap-4 min-w-0">
                      <div>
                        <p className="text-xs text-gray-400 mb-0.5">Entrada</p>
                        <code className="text-xs text-gray-700 bg-gray-50 px-2 py-1 rounded block whitespace-pre-wrap">{tc.input || '(vazia)'}</code>
                      </div>
                      <div>
                        <p className="text-xs text-gray-400 mb-0.5">Saída esperada</p>
                        <code className="text-xs text-gray-700 bg-gray-50 px-2 py-1 rounded block whitespace-pre-wrap">{tc.expected_output}</code>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => startEdit(tc)}
                        className="p-1.5 rounded-md text-gray-400 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                        title="Editar"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => confirmDelete(tc.id)}
                        disabled={deletingId === tc.id}
                        className="p-1.5 rounded-md text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors disabled:opacity-40"
                        title="Excluir"
                      >
                        {deletingId === tc.id
                          ? <Spinner className="w-3.5 h-3.5" />
                          : (
                            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                            </svg>
                          )
                        }
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Adicionar novos */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
        <h2 className="text-sm font-medium text-gray-700 mb-3">Adicionar caso de teste</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Entrada (stdin)</label>
            <textarea
              rows={4}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ex: 5 3"
              className="w-full text-sm font-mono rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Saída esperada (stdout)</label>
            <textarea
              rows={4}
              value={expected}
              onChange={e => setExpected(e.target.value)}
              placeholder="Ex: 8"
              className="w-full text-sm font-mono rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
          </div>
        </div>
        <button
          onClick={addLocal}
          disabled={!input.trim() || !expected.trim()}
          className="mt-3 text-sm px-3 py-1.5 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          + Adicionar à lista
        </button>
      </div>

      {pending.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100 mb-4">
          {pending.map((tc, i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-3">
              <span className="text-xs text-gray-300 shrink-0">novo</span>
              <div className="flex-1 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-400 mb-0.5">Entrada</p>
                  <code className="text-xs text-gray-700 bg-gray-50 px-2 py-1 rounded block truncate">{tc.input || '(vazia)'}</code>
                </div>
                <div>
                  <p className="text-xs text-gray-400 mb-0.5">Saída esperada</p>
                  <code className="text-xs text-gray-700 bg-gray-50 px-2 py-1 rounded block truncate">{tc.expected_output}</code>
                </div>
              </div>
              <button onClick={() => removePending(i)} className="text-gray-300 hover:text-red-400 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      {saveSuccess && (
        <div className="mb-3 rounded-lg bg-green-50 border border-green-200 px-4 py-2.5 text-sm text-green-700">
          Test cases salvos com sucesso.
        </div>
      )}

      <div className="flex items-center gap-3">
        <button
          onClick={save}
          disabled={saving || pending.length === 0}
          className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {saving && <Spinner className="w-4 h-4" />}
          Salvar {pending.length > 0 && `(${pending.length})`}
        </button>
        <Link to={`/exam/${id}`} className="text-sm text-gray-400 hover:text-gray-600">
          Voltar
        </Link>
      </div>
    </div>
  )
}
