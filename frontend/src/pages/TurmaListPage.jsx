import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listTurmas, createTurma, updateTurma, deleteTurma } from '../api/exam'
import Spinner from '../components/Spinner'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import ListControls from '../components/ListControls'

const SORT_OPTIONS = [
  { value: 'recent', label: 'Mais recentes' },
  { value: 'oldest', label: 'Mais antigas' },
  { value: 'name', label: 'Nome (A–Z)' },
]

export default function TurmaListPage() {
  const navigate = useNavigate()
  const [turmas, setTurmas] = useState([])
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('recent')
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [nome, setNome] = useState('')
  const [codigo, setCodigo] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  // edição / exclusão
  const [editTurma, setEditTurma] = useState(null)
  const [editNome, setEditNome] = useState('')
  const [editCodigo, setEditCodigo] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const openEdit = (t) => { setEditTurma(t); setEditNome(t.nome); setEditCodigo(t.codigo) }

  const saveEdit = async (e) => {
    e.preventDefault()
    if (!editNome.trim() || !editCodigo.trim()) return
    setSaving(true)
    try {
      await updateTurma(editTurma.id, editNome.trim(), editCodigo.trim())
      setTurmas(prev => prev.map(t => t.id === editTurma.id
        ? { ...t, nome: editNome.trim(), codigo: editCodigo.trim() } : t))
      setEditTurma(null)
    } catch {
      setError('Erro ao salvar turma.')
    } finally {
      setSaving(false)
    }
  }

  const confirmDelete = async () => {
    setDeleting(true)
    try {
      await deleteTurma(deleteTarget.id)
      setTurmas(prev => prev.filter(t => t.id !== deleteTarget.id))
      setDeleteTarget(null)
    } catch {
      setError('Erro ao excluir turma.')
    } finally {
      setDeleting(false)
    }
  }

  useEffect(() => {
    listTurmas()
      .then(({ data }) => setTurmas(data))
      .catch(() => setError('Erro ao carregar turmas.'))
      .finally(() => setLoading(false))
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    if (!nome.trim() || !codigo.trim()) return
    setCreating(true)
    setError('')
    try {
      const { data } = await createTurma(nome.trim(), codigo.trim())
      setTurmas(prev => [{ ...data, exam_count: data.exams?.length ?? 0 }, ...prev])
      setNome('')
      setCodigo('')
      setShowForm(false)
    } catch {
      setError('Erro ao criar turma.')
    } finally {
      setCreating(false)
    }
  }

  const formatDate = (iso) => {
    if (!iso) return ''
    return new Date(iso).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  const displayed = turmas
    .filter(t => {
      const q = search.trim().toLowerCase()
      if (!q) return true
      return t.nome.toLowerCase().includes(q) || t.codigo.toLowerCase().includes(q)
    })
    .sort((a, b) => {
      if (sort === 'name') return a.nome.localeCompare(b.nome, 'pt-BR')
      const da = new Date(a.created_at).getTime()
      const db = new Date(b.created_at).getTime()
      return sort === 'oldest' ? da - db : db - da
    })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Turmas</h1>
        <button
          onClick={() => setShowForm(v => !v)}
          className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Nova turma
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h2 className="text-sm font-medium text-gray-700 mb-4">Nova turma</h2>
          <form onSubmit={handleCreate} className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={nome}
              onChange={e => setNome(e.target.value)}
              placeholder="Nome da turma"
              className="flex-1 text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <input
              type="text"
              value={codigo}
              onChange={e => setCodigo(e.target.value)}
              placeholder="Código (ex: CS1-2026-1)"
              className="flex-1 text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
            <button
              type="submit"
              disabled={creating || !nome.trim() || !codigo.trim()}
              className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {creating && <Spinner className="w-4 h-4" />}
              Criar
            </button>
          </form>
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700 mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="w-6 h-6 text-purple-600" />
        </div>
      ) : turmas.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <svg className="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
          </svg>
          <p className="text-sm">Nenhuma turma cadastrada.</p>
          <p className="text-xs mt-1">Clique em "Nova turma" para começar.</p>
        </div>
      ) : (
        <>
          <ListControls
            search={search} onSearch={setSearch}
            sort={sort} onSort={setSort}
            sortOptions={SORT_OPTIONS}
            placeholder="Buscar turma por nome ou código…"
          />
          {displayed.length === 0 ? (
            <p className="text-center py-12 text-sm text-gray-400">Nenhuma turma encontrada para o filtro.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {displayed.map(t => (
            <div
              key={t.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:border-purple-300 hover:shadow-sm transition-all flex flex-col"
            >
              <div onClick={() => navigate(`/turma/${t.id}`)} className="cursor-pointer flex-1">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <h2 className="text-base font-semibold text-gray-900 leading-tight">{t.nome}</h2>
                  <span className="shrink-0 text-xs font-medium text-purple-700 bg-purple-50 border border-purple-100 px-2 py-0.5 rounded-md">
                    {t.codigo}
                  </span>
                </div>
                <p className="text-sm text-gray-500">{t.exam_count} {t.exam_count === 1 ? 'prova' : 'provas'}</p>
                <p className="text-xs text-gray-400 mt-1">{formatDate(t.created_at)}</p>
              </div>
              <div className="flex gap-2 mt-4 pt-3 border-t border-gray-100">
                <button
                  onClick={() => openEdit(t)}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
                >
                  Editar
                </button>
                <button
                  onClick={() => setDeleteTarget(t)}
                  className="text-xs px-2.5 py-1.5 rounded-md border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
                >
                  Excluir
                </button>
              </div>
            </div>
              ))}
            </div>
          )}
        </>
      )}

      <Modal open={!!editTurma} onClose={() => setEditTurma(null)} title="Editar turma">
        <form onSubmit={saveEdit} className="space-y-3">
          <input
            type="text" value={editNome} onChange={e => setEditNome(e.target.value)}
            placeholder="Nome da turma"
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <input
            type="text" value={editCodigo} onChange={e => setEditCodigo(e.target.value)}
            placeholder="Código"
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <div className="flex justify-end gap-2 pt-1">
            <button type="button" onClick={() => setEditTurma(null)}
              className="text-sm px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving || !editNome.trim() || !editCodigo.trim()}
              className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors">
              {saving && <Spinner className="w-4 h-4" />}
              Salvar
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={confirmDelete}
        loading={deleting}
        title="Excluir turma"
        confirmLabel="Excluir turma"
        message={deleteTarget
          ? `Excluir a turma "${deleteTarget.nome}"? Todas as provas, questões e submissões dela serão removidas permanentemente.`
          : ''}
      />
    </div>
  )
}
