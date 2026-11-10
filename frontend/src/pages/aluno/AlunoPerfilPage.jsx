import { useState } from 'react'
import { changeAlunoPassword, updateAlunoMe } from '../../api/aluno'
import Spinner from '../../components/Spinner'
import Botao from '../../components/ui/Botao'
import Card from '../../components/ui/Card'
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
      <h1 className="titulo-pagina">Meu perfil</h1>

      <Card as="form" onSubmit={salvarPerfil}>
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1.5">E-mail</label>
          <input type="email" value={aluno?.email || ''} disabled className="campo disabled:bg-lavanda disabled:text-cinza-texto" />
        </div>
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1.5">Nome</label>
          <input type="text" value={nome} onChange={e => setNome(e.target.value)} required className="campo" />
        </div>
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1.5">Matrícula</label>
          <input type="text" value={matricula} onChange={e => setMatricula(e.target.value)} className="campo" />
        </div>
        {erroPerfil && <p className="text-xs text-erro">{erroPerfil}</p>}
        {msgPerfil && <p className="text-xs text-sucesso">{msgPerfil}</p>}
        <div>
          <Botao type="submit" disabled={salvando}>
            {salvando && <Spinner className="w-4 h-4" />}
            Salvar
          </Botao>
        </div>
      </Card>

      <Card as="form" onSubmit={trocarSenha}>
        <h2 className="titulo-card">Trocar senha</h2>
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1.5">Senha atual</label>
          <input type="password" value={senhaAtual} onChange={e => setSenhaAtual(e.target.value)} required className="campo" />
        </div>
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1.5">Nova senha</label>
          <input type="password" value={senhaNova} onChange={e => setSenhaNova(e.target.value)} required className="campo" />
        </div>
        {erroSenha && <p className="text-xs text-erro">{erroSenha}</p>}
        {msgSenha && <p className="text-xs text-sucesso">{msgSenha}</p>}
        <div>
          <Botao type="submit" variante="secundario" disabled={trocando}>
            {trocando && <Spinner className="w-4 h-4" />}
            Trocar senha
          </Botao>
        </div>
      </Card>
    </div>
  )
}
