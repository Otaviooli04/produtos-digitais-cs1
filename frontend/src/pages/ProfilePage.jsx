import { useState } from 'react'
import { Link } from 'react-router-dom'
import { updateProfile, changePassword } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import Spinner from '../components/Spinner'

export default function ProfilePage() {
  const { professor, updateProfessor } = useAuth()
  const [nome, setNome] = useState(professor?.nome ?? '')
  const [savingNome, setSavingNome] = useState(false)
  const [nomeMsg, setNomeMsg] = useState('')

  const [atual, setAtual] = useState('')
  const [nova, setNova] = useState('')
  const [savingPwd, setSavingPwd] = useState(false)
  const [pwdMsg, setPwdMsg] = useState('')
  const [pwdErr, setPwdErr] = useState('')

  const saveNome = async (e) => {
    e.preventDefault()
    if (!nome.trim()) return
    setSavingNome(true); setNomeMsg('')
    try {
      const { data } = await updateProfile(nome.trim())
      updateProfessor(data)
      setNomeMsg('Nome atualizado.')
    } catch {
      setNomeMsg('Erro ao atualizar o nome.')
    } finally {
      setSavingNome(false)
    }
  }

  const savePwd = async (e) => {
    e.preventDefault()
    if (!atual || !nova) return
    setSavingPwd(true); setPwdMsg(''); setPwdErr('')
    try {
      await changePassword(atual, nova)
      setPwdMsg('Senha alterada com sucesso.')
      setAtual(''); setNova('')
    } catch (err) {
      setPwdErr(err.response?.data?.detail || 'Erro ao alterar a senha.')
    } finally {
      setSavingPwd(false)
    }
  }

  const input = "w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
  const btn = "inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors"

  return (
    <div className="max-w-lg mx-auto">
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to="/" className="hover:text-gray-600">Turmas</Link>
        <span>›</span>
        <span className="text-gray-600">Meu perfil</span>
      </div>

      <h1 className="text-xl font-semibold text-gray-900 mb-6">Meu perfil</h1>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-5">
        <h2 className="text-sm font-medium text-gray-700 mb-4">Dados</h2>
        <form onSubmit={saveNome} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">E-mail</label>
            <input type="text" value={professor?.email ?? ''} disabled
              className={`${input} bg-gray-50 text-gray-400`} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Nome</label>
            <input type="text" value={nome} onChange={e => setNome(e.target.value)} className={input} />
          </div>
          {nomeMsg && <p className="text-xs text-gray-500">{nomeMsg}</p>}
          <div className="flex justify-end">
            <button type="submit" disabled={savingNome || !nome.trim()} className={btn}>
              {savingNome && <Spinner className="w-4 h-4" />}
              Salvar
            </button>
          </div>
        </form>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-medium text-gray-700 mb-4">Alterar senha</h2>
        <form onSubmit={savePwd} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Senha atual</label>
            <input type="password" value={atual} onChange={e => setAtual(e.target.value)} className={input} />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Nova senha</label>
            <input type="password" value={nova} onChange={e => setNova(e.target.value)} className={input} />
          </div>
          {pwdMsg && <p className="text-xs text-green-600">{pwdMsg}</p>}
          {pwdErr && <p className="text-xs text-red-600">{pwdErr}</p>}
          <div className="flex justify-end">
            <button type="submit" disabled={savingPwd || !atual || !nova} className={btn}>
              {savingPwd && <Spinner className="w-4 h-4" />}
              Alterar senha
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
