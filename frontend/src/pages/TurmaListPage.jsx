import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Pencil, Plus, Trash2, Users } from 'lucide-react'
import { listTurmas, createTurma, updateTurma, deleteTurma } from '../api/exam'
import Spinner from '../components/Spinner'
import Modal from '../components/Modal'
import ConfirmDialog from '../components/ConfirmDialog'
import ListControls from '../components/ListControls'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import Tag from '../components/ui/Tag'

const SORT_OPTIONS = [
  { value: 'recent', label: 'Mais recentes' },
  { value: 'oldest', label: 'Mais antigas' },
  { value: 'name', label: 'Nome (A–Z)' },
]

// Campo vazio é "não informado", que o backend guarda como nulo.
const paraAlunos = (valor) => (valor === '' ? null : Number(valor))

export default function TurmaListPage() {
  const [turmas, setTurmas] = useState([])
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState('recent')
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [nome, setNome] = useState('')
  const [codigo, setCodigo] = useState('')
  const [alunosPrevistos, setAlunosPrevistos] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  // edição / exclusão
  const [editTurma, setEditTurma] = useState(null)
  const [editNome, setEditNome] = useState('')
  const [editCodigo, setEditCodigo] = useState('')
  const [editAlunos, setEditAlunos] = useState('')
  const [saving, setSaving] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)

  const openEdit = (t) => {
    setEditTurma(t)
    setEditNome(t.nome)
    setEditCodigo(t.codigo)
    setEditAlunos(t.alunos_previstos ?? '')
  }

  const saveEdit = async (e) => {
    e.preventDefault()
    if (!editNome.trim() || !editCodigo.trim()) return
    setSaving(true)
    try {
      await updateTurma(editTurma.id, editNome.trim(), editCodigo.trim(), paraAlunos(editAlunos))
      setTurmas(prev => prev.map(t => t.id === editTurma.id
        ? { ...t, nome: editNome.trim(), codigo: editCodigo.trim(), alunos_previstos: paraAlunos(editAlunos) }
        : t))
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
      const { data } = await createTurma(nome.trim(), codigo.trim(), paraAlunos(alunosPrevistos))
      setTurmas(prev => [{ ...data, exam_count: data.exams?.length ?? 0 }, ...prev])
      setNome('')
      setCodigo('')
      setAlunosPrevistos('')
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
      <div className="flex items-center justify-between gap-3 mb-6">
        <h1 className="titulo-pagina">Turmas</h1>
        <Botao onClick={() => setShowForm(v => !v)}>
          <Plus className="w-4 h-4" aria-hidden="true" />
          Nova turma
        </Botao>
      </div>

      {showForm && (
        <Card as="form" onSubmit={handleCreate} className="mb-6">
          <h2 className="titulo-card">Nova turma</h2>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              value={nome}
              onChange={e => setNome(e.target.value)}
              placeholder="Nome da turma"
              className="campo flex-1"
            />
            <input
              type="text"
              value={codigo}
              onChange={e => setCodigo(e.target.value)}
              placeholder="Código (ex: CS1-2026-1)"
              className="campo flex-1"
            />
            <input
              type="number"
              min={1}
              max={1000}
              value={alunosPrevistos}
              onChange={e => setAlunosPrevistos(e.target.value)}
              placeholder="Alunos na turma (opcional)"
              className="campo sm:w-56!"
            />
            <Botao type="submit" disabled={creating || !nome.trim() || !codigo.trim()}>
              {creating && <Spinner className="w-4 h-4" />}
              Criar
            </Botao>
          </div>
        </Card>
      )}

      {error && (
        <div className="rounded-botao bg-erro-fundo border-2 border-erro px-4 py-3 text-sm text-erro mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner className="w-6 h-6 text-violeta" />
        </div>
      ) : turmas.length === 0 ? (
        <Card className="border-dashed border-noite/30! items-center text-center py-16!">
          <Users className="w-10 h-10 text-violeta" aria-hidden="true" />
          <p className="text-sm text-cinza-texto">Nenhuma turma cadastrada.</p>
          <p className="text-xs text-cinza-texto">Clique em "Nova turma" para começar.</p>
        </Card>
      ) : (
        <>
          <ListControls
            search={search} onSearch={setSearch}
            sort={sort} onSort={setSort}
            sortOptions={SORT_OPTIONS}
            placeholder="Buscar turma por nome ou código…"
          />
          {displayed.length === 0 ? (
            <p className="text-center py-12 text-sm text-cinza-texto">Nenhuma turma encontrada para o filtro.</p>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {displayed.map(t => (
                <Card key={t.id} principal className="gap-0!">
                  <Link to={`/turma/${t.id}`} className="flex-1 flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                      <h2 className="titulo-card text-xl!">{t.nome}</h2>
                      <Tag>{t.codigo}</Tag>
                    </div>
                    <p className="text-sm text-cinza-texto">{t.exam_count} {t.exam_count === 1 ? 'atividade' : 'atividades'}</p>
                    <p className="text-xs text-cinza-texto">{formatDate(t.created_at)}</p>
                  </Link>
                  <div className="flex gap-1 mt-3 pt-2 border-t-2 border-noite/10">
                    <button
                      onClick={() => openEdit(t)}
                      aria-label={`Editar a turma ${t.nome}`}
                      className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-botao border-2 border-transparent text-noite hover:border-noite hover:bg-lavanda"
                    >
                      <Pencil className="w-4 h-4" aria-hidden="true" />
                    </button>
                    <button
                      onClick={() => setDeleteTarget(t)}
                      aria-label={`Excluir a turma ${t.nome}`}
                      className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-botao border-2 border-transparent text-erro hover:border-erro hover:bg-erro-fundo"
                    >
                      <Trash2 className="w-4 h-4" aria-hidden="true" />
                    </button>
                  </div>
                </Card>
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
            className="campo"
          />
          <input
            type="text" value={editCodigo} onChange={e => setEditCodigo(e.target.value)}
            placeholder="Código"
            className="campo"
          />
          <label className="block text-xs text-cinza-texto">
            Alunos na turma (opcional)
            <input
              type="number" min={1} max={1000} value={editAlunos} onChange={e => setEditAlunos(e.target.value)}
              className="campo mt-1"
            />
          </label>
          <div className="flex justify-end gap-2 pt-1">
            <Botao variante="secundario" onClick={() => setEditTurma(null)}>Cancelar</Botao>
            <Botao type="submit" disabled={saving || !editNome.trim() || !editCodigo.trim()}>
              {saving && <Spinner className="w-4 h-4" />}
              Salvar
            </Botao>
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
