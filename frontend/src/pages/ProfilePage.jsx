import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import { updateProfile, changePassword } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import Spinner from '../components/Spinner'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'

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

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto lg:hidden">
        <Link to="/" className="hover:text-noite">Turmas</Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <span>Meu perfil</span>
      </div>

      <h1 className="titulo-pagina">Meu perfil</h1>

      <Card>
        <h2 className="titulo-card">Dados</h2>
        <form onSubmit={saveNome} className="space-y-3">
          <div>
            <label className="block text-xs font-bold text-cinza-texto mb-1">E-mail</label>
            <input type="text" value={professor?.email ?? ''} disabled
              className="campo bg-lavanda! text-cinza-texto!" />
          </div>
          <div>
            <label className="block text-xs font-bold text-cinza-texto mb-1">Nome</label>
            <input type="text" value={nome} onChange={e => setNome(e.target.value)} className="campo" />
          </div>
          {nomeMsg && <p className="text-xs text-cinza-texto">{nomeMsg}</p>}
          <div className="flex justify-end">
            <Botao type="submit" disabled={savingNome || !nome.trim()}>
              {savingNome && <Spinner className="w-4 h-4" />}
              Salvar
            </Botao>
          </div>
        </form>
      </Card>

      <Card>
        <h2 className="titulo-card">Alterar senha</h2>
        <form onSubmit={savePwd} className="space-y-3">
          <div>
            <label className="block text-xs font-bold text-cinza-texto mb-1">Senha atual</label>
            <input type="password" value={atual} onChange={e => setAtual(e.target.value)} className="campo" />
          </div>
          <div>
            <label className="block text-xs font-bold text-cinza-texto mb-1">Nova senha</label>
            <input type="password" value={nova} onChange={e => setNova(e.target.value)} className="campo" />
          </div>
          {pwdMsg && <p className="text-xs text-sucesso">{pwdMsg}</p>}
          {pwdErr && <p className="text-xs text-erro">{pwdErr}</p>}
          <div className="flex justify-end">
            <Botao type="submit" disabled={savingPwd || !atual || !nova}>
              {savingPwd && <Spinner className="w-4 h-4" />}
              Alterar senha
            </Botao>
          </div>
        </form>
      </Card>
    </div>
  )
}
