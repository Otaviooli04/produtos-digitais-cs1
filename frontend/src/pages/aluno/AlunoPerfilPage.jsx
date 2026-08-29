import { useState } from 'react'
import { changeAlunoPassword, updateAlunoMe } from '../../api/aluno'
import Spinner from '../../components/Spinner'
import { useAlunoAuth } from '../../context/AlunoAuthContext'

export default function AlunoPerfilPage() {
  const { aluno, updateAluno } = useAlunoAuth()
  const [nome, setNome] = useState(aluno?.nome || '')
  const [matricula, setMatricula] = useState(aluno?.matricula || '')
  const [salvando, setSalvando] = useState(false)
  const [msgPerfil, setMsgPerfil] = useState('')
  const [erroPerfil, setErroPerfil] = useState('')

  const [senhaAtual, setSenhaAtual] = useState('')
  const [senhaNova, setSenhaNova] = useState('')
  const [trocando, setTrocando] = useState(false)
  const [msgSenha, setMsgSenha] = useState('')
  const [erroSenha, setErroSenha] = useState('')

  const campo = 'w-full text-sm rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'

  const salvarPerfil = async (e) => {
    e.preventDefault()
    setMsgPerfil(''); setErroPerfil(''); setSalvando(true)
    try {
      const { data } = await updateAlunoMe(nome.trim(), matricula.trim())
      updateAluno(data)
      setMsgPerfil('Dados atualizados.')
    } catch (err) {
      setErroPerfil(err.response?.data?.detail || 'Não foi possível salvar.')
    } finally {
      setSalvando(false)
    }
  }

  const trocarSenha = async (e) => {
    e.preventDefault()
    setMsgSenha(''); setErroSenha(''); setTrocando(true)
    try {
      await changeAlunoPassword(senhaAtual, senhaNova)
      setSenhaAtual(''); setSenhaNova('')
      setMsgSenha('Senha alterada.')
    } catch (err) {
      setErroSenha(err.response?.data?.detail || 'Não foi possível trocar a senha.')
    } finally {
      setTrocando(false)
    }
  }

  return (
    <div className="max-w-md space-y-6">
      <h1 className="text-xl font-semibold text-gray-900">Meu perfil</h1>

      <form onSubmit={salvarPerfil} className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">E-mail</label>
          <input type="email" value={aluno?.email || ''} disabled className={`${campo} bg-gray-50 text-gray-400`} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Nome</label>
          <input type="text" value={nome} onChange={e => setNome(e.target.value)} required className={campo} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Matrícula</label>
          <input type="text" value={matricula} onChange={e => setMatricula(e.target.value)} className={campo} />
        </div>
        {erroPerfil && <p className="text-xs text-red-600">{erroPerfil}</p>}
        {msgPerfil && <p className="text-xs text-green-600">{msgPerfil}</p>}
        <button
          type="submit"
          disabled={salvando}
          className="inline-flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-40 transition-colors"
        >
          {salvando && <Spinner className="w-4 h-4" />}
          Salvar
        </button>
      </form>

      <form onSubmit={trocarSenha} className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
        <h2 className="text-sm font-semibold text-gray-900">Trocar senha</h2>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Senha atual</label>
          <input type="password" value={senhaAtual} onChange={e => setSenhaAtual(e.target.value)} required className={campo} />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Nova senha</label>
          <input type="password" value={senhaNova} onChange={e => setSenhaNova(e.target.value)} required className={campo} />
        </div>
        {erroSenha && <p className="text-xs text-red-600">{erroSenha}</p>}
        {msgSenha && <p className="text-xs text-green-600">{msgSenha}</p>}
        <button
          type="submit"
          disabled={trocando}
          className="inline-flex items-center gap-2 text-sm px-4 py-2.5 rounded-xl border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition-colors"
        >
          {trocando && <Spinner className="w-4 h-4" />}
          Trocar senha
        </button>
      </form>
    </div>
  )
}
