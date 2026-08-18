import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { loginAluno } from '../../api/aluno'
import { useAlunoAuth } from '../../context/AlunoAuthContext'
import Logo from '../../components/Logo'

export default function AlunoLoginPage() {
  const { login } = useAlunoAuth()
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
      const { data } = await loginAluno(email.trim(), senha)
      login(data.access_token, data.aluno)
      navigate('/aluno', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao entrar.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <Logo className="w-8 h-8" />
          <span className="font-semibold text-gray-900">Analytics CS1</span>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-8">
          <h1 className="text-lg font-semibold text-gray-900 mb-1">Entrar</h1>
          <p className="text-sm text-gray-400 mb-6">Área do aluno</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">E-mail</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="aluno@unifei.edu.br"
                autoComplete="email"
                required
                className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Senha</label>
              <input
                type="password"
                value={senha}
                onChange={e => setSenha(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
                required
                className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-2.5 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full text-sm py-2.5 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? 'Entrando…' : 'Entrar'}
            </button>
          </form>

          <p className="mt-5 text-center text-xs text-gray-400">
            Primeira vez?{' '}
            <Link to="/aluno/cadastro" className="text-purple-600 hover:underline font-medium">
              Criar conta
            </Link>
          </p>
          <p className="mt-2 text-center text-xs text-gray-400">
            É professor?{' '}
            <Link to="/login" className="text-gray-500 hover:underline">
              Entrar no painel
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
