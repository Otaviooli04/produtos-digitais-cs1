import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { loginAluno } from '../../api/aluno'
import { useAlunoAuth } from '../../context/AlunoAuthContext'
import Botao from '../../components/ui/Botao'
import Card from '../../components/ui/Card'
import TelaDeEntrada from '../../components/TelaDeEntrada'
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
    <TelaDeEntrada frase="Entenda o seu erro e tente de novo.">
      <Card principal>
        <SeletorPerfil atual="aluno" contexto="login" />
        <h1 className="titulo-pagina">Entrar</h1>
        <p className="text-sm text-cinza-texto mb-6">Suas atividades e seu progresso</p>

        {convite && (
          <div className="rounded-botao bg-lavanda border-2 border-noite/20 px-4 py-2.5 text-sm text-violeta mb-4">
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
          Primeira vez?{' '}
          <Link to="/aluno/cadastro" className="text-violeta hover:underline font-medium">
            Criar conta
          </Link>
        </p>
      </Card>
    </TelaDeEntrada>
  )
}
