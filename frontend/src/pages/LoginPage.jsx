import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login as apiLogin } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import Botao from '../components/ui/Botao'
import Card from '../components/ui/Card'
import TelaDeEntrada from '../components/TelaDeEntrada'
import SeletorPerfil from '../components/SeletorPerfil'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim() || !senha.trim()) return
    setError('')
    setLoading(true)
    try {
      const { data } = await apiLogin(email.trim(), senha)
      login(data.access_token, data.professor)
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao fazer login.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <TelaDeEntrada frase="Veja onde a turma trava e ajude por grupo.">
      <Card principal>
        <SeletorPerfil atual="professor" contexto="login" />
        <h1 className="titulo-pagina">Entrar</h1>
        <p className="text-sm text-cinza-texto mb-6">Suas turmas e correções</p>

        <form onSubmit={handleSubmit} className="space-y-4">
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
              placeholder="••••••••"
              autoComplete="current-password"
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
            {loading ? 'Entrando…' : 'Entrar'}
          </Botao>
        </form>

        <p className="mt-5 text-center text-xs text-cinza-texto">
          Sem conta?{' '}
          <Link to="/register" className="text-violeta hover:underline font-medium">
            Criar cadastro
          </Link>
        </p>
      </Card>
    </TelaDeEntrada>
  )
}
