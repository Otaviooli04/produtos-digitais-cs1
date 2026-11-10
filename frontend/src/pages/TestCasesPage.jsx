import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import LinkDaAtividade from '../components/LinkDaAtividade'
import { ChevronRight, Pencil, Plus, Trash2, X } from 'lucide-react'
import { getExam, getTestCases, addTestCases, updateTestCase, deleteTestCase } from '../api/exam'
import Spinner from '../components/Spinner'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import RotuloSecao from '../components/ui/RotuloSecao'
import Tag from '../components/ui/Tag'

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

  // eslint-disable-next-line react-hooks/set-state-in-effect, react-hooks/exhaustive-deps -- carga ao abrir a questão
  useEffect(() => { loadData() }, [id, num])

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

  if (!question) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>

  return (
    <div className="max-w-2xl">
      <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto mb-6 lg:hidden">
        <LinkDaAtividade id={id} />
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <span>Questão {num}</span>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <span>Test cases</span>
      </div>

      <h1 className="titulo-pagina mb-1">Test cases</h1>
      <p className="text-sm text-cinza-texto line-clamp-2 mb-6">{question.statement}</p>

      {/* Cadastrados */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <RotuloSecao as="h2">Cadastrados</RotuloSecao>
          {!loadingSaved && <Tag variante="neutro">{saved.length}</Tag>}
        </div>

        {loadingSaved ? (
          <div className="flex justify-center py-6"><Spinner className="w-5 h-5 text-violeta" /></div>
        ) : saved.length === 0 ? (
          <Card className="border-dashed border-noite/30! text-center text-sm text-cinza-texto py-4!">
            Nenhum test case cadastrado ainda.
          </Card>
        ) : (
          <div className="bg-white rounded-card border-2 border-noite divide-y-2 divide-noite/10 overflow-hidden">
            {saved.map((tc, i) => (
              <div key={tc.id} className="px-5 py-3">
                {editingId === tc.id ? (
                  <div>
                    <div className="grid grid-cols-2 gap-3 mb-2">
                      <div>
                        <label className="block text-xs text-cinza-texto mb-1">Entrada</label>
                        <textarea
                          rows={3}
                          value={editInput}
                          onChange={e => setEditInput(e.target.value)}
                          className="campo font-mono resize-none"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-cinza-texto mb-1">Saída esperada</label>
                        <textarea
                          rows={3}
                          value={editExpected}
                          onChange={e => setEditExpected(e.target.value)}
                          className="campo font-mono resize-none"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Botao onClick={() => confirmEdit(tc)}>Salvar</Botao>
                      <Botao variante="secundario" onClick={cancelEdit}>Cancelar</Botao>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center gap-4">
                    <span className="text-xs text-cinza-texto shrink-0 w-5">#{i + 1}</span>
                    <div className="flex-1 grid grid-cols-2 gap-4 min-w-0">
                      <div>
                        <p className="text-xs text-cinza-texto mb-0.5">Entrada</p>
                        <code className="text-xs text-cinza-texto bg-lavanda px-2 py-1 rounded-botao block whitespace-pre-wrap">{tc.input || '(vazia)'}</code>
                      </div>
                      <div>
                        <p className="text-xs text-cinza-texto mb-0.5">Saída esperada</p>
                        <code className="text-xs text-cinza-texto bg-lavanda px-2 py-1 rounded-botao block whitespace-pre-wrap">{tc.expected_output}</code>
                      </div>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => startEdit(tc)}
                        className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-botao border-2 border-transparent text-noite hover:border-noite hover:bg-lavanda"
                        aria-label="Editar"
                      >
                        <Pencil className="w-4 h-4" aria-hidden="true" />
                      </button>
                      <button
                        onClick={() => confirmDelete(tc.id)}
                        disabled={deletingId === tc.id}
                        className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-botao border-2 border-transparent text-erro hover:border-erro hover:bg-erro-fundo disabled:opacity-50"
                        aria-label="Excluir"
                      >
                        {deletingId === tc.id
                          ? <Spinner className="w-4 h-4" />
                          : <Trash2 className="w-4 h-4" aria-hidden="true" />
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
      <Card className="mb-4">
        <h2 className="titulo-card">Adicionar caso de teste</h2>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-cinza-texto mb-1">Entrada (stdin)</label>
            <textarea
              rows={4}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ex: 5 3"
              className="campo font-mono resize-none"
            />
          </div>
          <div>
            <label className="block text-xs text-cinza-texto mb-1">Saída esperada (stdout)</label>
            <textarea
              rows={4}
              value={expected}
              onChange={e => setExpected(e.target.value)}
              placeholder="Ex: 8"
              className="campo font-mono resize-none"
            />
          </div>
        </div>
        <div>
          <Botao variante="secundario" onClick={addLocal} disabled={!input.trim() || !expected.trim()}>
            <Plus className="w-4 h-4" aria-hidden="true" />
            Adicionar à lista
          </Botao>
        </div>
      </Card>

      {pending.length > 0 && (
        <div className="bg-white rounded-card border-2 border-noite divide-y-2 divide-noite/10 overflow-hidden mb-4">
          {pending.map((tc, i) => (
            <div key={i} className="flex items-center gap-4 px-5 py-3">
              <span className="text-xs text-cinza-texto shrink-0">novo</span>
              <div className="flex-1 min-w-0 grid grid-cols-2 gap-4">
                <div className="min-w-0">
                  <p className="text-xs text-cinza-texto mb-0.5">Entrada</p>
                  <code className="text-xs text-cinza-texto bg-lavanda px-2 py-1 rounded-botao block truncate">{tc.input || '(vazia)'}</code>
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-cinza-texto mb-0.5">Saída esperada</p>
                  <code className="text-xs text-cinza-texto bg-lavanda px-2 py-1 rounded-botao block truncate">{tc.expected_output}</code>
                </div>
              </div>
              <button
                onClick={() => removePending(i)}
                className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-botao border-2 border-transparent text-noite hover:border-erro hover:bg-erro-fundo hover:text-erro"
                aria-label="Remover da lista"
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-erro mb-3">{error}</p>}

      {saveSuccess && (
        <div className="mb-3 rounded-botao bg-sucesso-fundo border-2 border-sucesso px-4 py-2.5 text-sm text-sucesso">
          Test cases salvos com sucesso.
        </div>
      )}

      <div className="flex items-center gap-3">
        <Botao onClick={save} disabled={saving || pending.length === 0}>
          {saving && <Spinner className="w-4 h-4" />}
          Salvar {pending.length > 0 && `(${pending.length})`}
        </Botao>
        <Link to={`/exam/${id}`} className="text-sm font-bold text-cinza-texto hover:text-noite">
          Voltar
        </Link>
      </div>
    </div>
  )
}
