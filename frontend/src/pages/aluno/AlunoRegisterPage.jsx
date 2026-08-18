import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerAluno } from '../../api/aluno'
import { useAlunoAuth } from '../../context/AlunoAuthContext'
import Logo from '../../components/Logo'

export default function AlunoRegisterPage() {
  const { login } = useAlunoAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ nome: '', email: '', matricula: '', senha: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (campo) => (e) => setForm(f => ({ ...f, [campo]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await registerAluno(
        form.email.trim(), form.nome.trim(), form.matricula.trim(), form.senha)
      login(data.access_token, data.aluno)
      navigate('/aluno', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao criar a conta.')
    } finally {
      setLoading(false)
    }
  }

  const campo = 'w-full text-sm rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent'

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2.5 mb-8">
          <Logo className="w-8 h-8" />
          <span className="font-semibold text-gray-900">Analytics CS1</span>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-8">
          <h1 className="text-lg font-semibold text-gray-900 mb-1">Criar conta</h1>
          <p className="text-sm text-gray-400 mb-6">Depois é só entrar na turma com o código do professor</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Nome</label>
              <input type="text" value={form.nome} onChange={set('nome')} required className={campo} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">E-mail</label>
              <input type="email" value={form.email} onChange={set('email')} autoComplete="email" required className={campo} />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Matrícula</label>
              <input
                type="text"
                value={form.matricula}
                onChange={set('matricula')}
                placeholder="Ex: 2026001"
                className={campo}
              />
              <p className="mt-1 text-xs text-gray-400">
                Serve para reencontrar as submissões que você já tinha enviado sem conta.
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5">Senha</label>
              <input type="password" value={form.senha} onChange={set('senha')} autoComplete="new-password" required className={campo} />
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
              {loading ? 'Criando…' : 'Criar conta'}
            </button>
          </form>

          <p className="mt-5 text-center text-xs text-gray-400">
            Já tem conta?{' '}
            <Link to="/aluno/login" className="text-purple-600 hover:underline font-medium">
              Entrar
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
