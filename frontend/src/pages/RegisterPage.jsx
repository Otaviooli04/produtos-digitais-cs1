import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register as apiRegister } from '../api/auth'
import { useAuth } from '../context/AuthContext'
import Logo from '../components/Logo'
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
    if (senha.length < 6) { setError('A senha deve ter no mínimo 6 caracteres.'); return }
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
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <Logo className="w-8 h-8" />
          <span className="font-semibold text-gray-900">Analytics CS1</span>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-8">
          <SeletorPerfil atual="professor" contexto="cadastro" />
          <h1 className="text-lg font-semibold text-gray-900 mb-1">Criar conta</h1>
          <p className="text-sm text-gray-400 mb-6">Para criar turmas e corrigir provas</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Nome completo</label>
              <input
                type="text"
                value={nome}
                onChange={e => setNome(e.target.value)}
                placeholder="Prof. João Silva"
                autoComplete="name"
                required
                className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">E-mail</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="professor@unifei.edu.br"
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
                placeholder="mínimo 6 caracteres"
                autoComplete="new-password"
                required
                className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Confirmar senha</label>
              <input
                type="password"
                value={confirma}
                onChange={e => setConfirma(e.target.value)}
                placeholder="••••••••"
                autoComplete="new-password"
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
              {loading ? 'Criando conta…' : 'Criar conta'}
            </button>
          </form>

          <p className="mt-5 text-center text-xs text-gray-400">
            Já tem conta?{' '}
            <Link to="/login" className="text-purple-600 hover:underline font-medium">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
