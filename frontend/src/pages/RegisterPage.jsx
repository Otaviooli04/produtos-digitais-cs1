import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register as apiRegister } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import TelaDeEntrada from '../components/TelaDeEntrada'
import SeletorPerfil from '../components/SeletorPerfil'

export default function RegisterPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [confirma, setConfirma] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (senha !== confirma) { setError('As senhas não conferem.'); return }
    if (senha.length < 8) { setError('A senha deve ter no mínimo 8 caracteres.'); return }
    setError('')
    setLoading(true)
    try {
      const { data } = await apiRegister(email.trim(), nome.trim(), senha)
      login(data.access_token, data.professor)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao criar conta.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <TelaDeEntrada frase="Veja onde a turma trava e ajude por grupo.">
      <Card principal>
        <SeletorPerfil atual="professor" contexto="cadastro" />
        <h1 className="titulo-pagina">Criar conta</h1>
        <p className="text-sm text-cinza-texto mb-6">Para criar turmas e corrigir provas</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">Nome completo</label>
            <input
              type="text"
              value={nome}
              onChange={e => setNome(e.target.value)}
              placeholder="Prof. João Silva"
              autoComplete="name"
              required
              className="campo"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">E-mail</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="professor@unifei.edu.br"
              autoComplete="email"
              required
              className="campo"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">Senha</label>
            <input
              type="password"
              value={senha}
              onChange={e => setSenha(e.target.value)}
              placeholder="mínimo 8 caracteres"
              minLength={8}
              autoComplete="new-password"
              required
              className="campo"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">Confirmar senha</label>
            <input
              type="password"
              value={confirma}
              onChange={e => setConfirma(e.target.value)}
              placeholder="••••••••"
              autoComplete="new-password"
              required
              className="campo"
            />
          </div>

          {error && (
            <div className="rounded-botao bg-erro-fundo border-2 border-erro px-4 py-2.5 text-sm text-erro">
              {error}
            </div>
          )}

          <Botao type="submit" disabled={loading} className="w-full">
            {loading ? 'Criando conta…' : 'Criar conta'}
          </Botao>
        </form>

        <p className="mt-5 text-center text-xs text-cinza-texto">
          Já tem conta?{' '}
          <Link to="/login" className="text-violeta hover:underline font-medium">
            Entrar
          </Link>
        </p>
      </Card>
    </TelaDeEntrada>
  )
}
