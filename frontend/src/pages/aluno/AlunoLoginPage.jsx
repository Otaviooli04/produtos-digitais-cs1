import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { loginAluno } from '../../api/aluno'
import { useAlunoAuth } from '../../context/AlunoAuthContext'
import Logo from '../../components/Logo'
import SeletorPerfil from '../../components/SeletorPerfil'
import { lerConvite } from '../../utils/convitePendente'

export default function AlunoLoginPage() {
  const { login } = useAlunoAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [convite] = useState(lerConvite)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email.trim() || !senha.trim()) return
    setError('')
    setLoading(true)
    try {
      const { data } = await loginAluno(email.trim(), senha)
      login(data.access_token, data.aluno)
      navigate(convite ? `/aluno/convite/${encodeURIComponent(convite)}` : '/aluno', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao entrar.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-lavanda flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <Logo className="w-8 h-8" />
          <span className="font-semibold text-noite">Analytics CS1</span>
        </div>

        <div className="bg-white rounded-2xl border border-noite/20 p-8">
          <SeletorPerfil atual="aluno" contexto="login" />
          <h1 className="text-lg font-semibold text-noite mb-1">Entrar</h1>
          <p className="text-sm text-cinza-texto mb-6">Suas atividades e seu progresso</p>

          {convite && (
            <div className="rounded-lg bg-lavanda border border-violeta/15 px-4 py-2.5 text-sm text-violeta mb-4">
              Depois de entrar, você vai direto para a turma.
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-cinza-texto mb-1.5">E-mail</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="aluno@unifei.edu.br"
                autoComplete="email"
                required
                className="w-full text-sm rounded-lg border border-noite/20 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-violeta focus:border-transparent"
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
                className="w-full text-sm rounded-lg border border-noite/20 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-violeta focus:border-transparent"
              />
            </div>

            {error && (
              <div className="rounded-lg bg-erro-fundo border border-erro/30 px-4 py-2.5 text-sm text-erro">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full text-sm py-2.5 rounded-xl bg-violeta text-white font-medium hover:bg-violeta-escuro disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>

          <p className="mt-5 text-center text-xs text-cinza-texto">
            Primeira vez?{' '}
            <Link to="/aluno/cadastro" className="text-violeta hover:underline font-medium">
              Criar conta
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
