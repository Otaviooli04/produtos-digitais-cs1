import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { registerAluno } from '../../api/aluno'
import { useAlunoAuth } from '../../context/AlunoAuthContext'
import Botao from '../../components/ui/Botao'
import Card from '../../components/ui/Card'
import TelaDeEntrada from '../../components/TelaDeEntrada'
import SeletorPerfil from '../../components/SeletorPerfil'
import { lerConvite } from '../../utils/convitePendente'

export default function AlunoRegisterPage() {
  const { login } = useAlunoAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ nome: '', email: '', matricula: '', senha: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [convite] = useState(lerConvite)

  const set = (campo) => (e) => setForm(f => ({ ...f, [campo]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await registerAluno(
        form.email.trim(), form.nome.trim(), form.matricula.trim(), form.senha)
      login(data.access_token, data.aluno)
      navigate(convite ? `/aluno/convite/${encodeURIComponent(convite)}` : '/aluno', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao criar a conta.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <TelaDeEntrada frase="Entenda o seu erro e tente de novo.">
      <Card principal>
        <SeletorPerfil atual="aluno" contexto="cadastro" />
        <h1 className="titulo-pagina">Criar conta</h1>
        <p className="text-sm text-cinza-texto mb-6">Depois é só entrar na turma com o código do professor</p>

        {convite && (
          <div className="rounded-botao bg-lavanda border-2 border-noite/20 px-4 py-2.5 text-sm text-violeta mb-4">
            Depois de entrar, você vai direto para a turma.
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">Nome</label>
            <input type="text" value={form.nome} onChange={set('nome')} required className="campo" />
          </div>
          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">E-mail</label>
            <input type="email" value={form.email} onChange={set('email')} autoComplete="email" required className="campo" />
          </div>
          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">Matrícula</label>
            <input
              type="text"
              value={form.matricula}
              onChange={set('matricula')}
              placeholder="Ex: 2026001"
              className="campo"
            />
            <p className="mt-1 text-xs text-cinza-texto">
              Serve para reencontrar as submissões que você já tinha enviado sem conta.
            </p>
          </div>
          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">Senha</label>
            <input type="password" value={form.senha} onChange={set('senha')} autoComplete="new-password" required minLength={8} placeholder="mínimo 8 caracteres" className="campo" />
          </div>

          {error && (
            <div className="rounded-botao bg-erro-fundo border-2 border-erro px-4 py-2.5 text-sm text-erro">
              {error}
            </div>
          )}

          <Botao type="submit" disabled={loading} className="w-full">
            {loading ? 'Criando…' : 'Criar conta'}
          </Botao>
        </form>

        <p className="mt-5 text-center text-xs text-cinza-texto">
          Já tem conta?{' '}
          <Link to="/aluno/login" className="text-violeta hover:underline font-medium">
            Entrar
          </Link>
        </p>
      </Card>
    </TelaDeEntrada>
  )
}
