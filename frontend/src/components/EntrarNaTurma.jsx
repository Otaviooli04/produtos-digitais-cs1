import { useState } from 'react'
import { entrarNaTurma } from '../api/aluno'
import Spinner from './Spinner'
import Botao from './ui/Botao'
import Card from './ui/Card'

export default function EntrarNaTurma({ aoEntrar }) {
  const [codigo, setCodigo] = useState('')
  const [entrando, setEntrando] = useState(false)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!codigo.trim()) return
    setErro('')
    setSucesso('')
    setEntrando(true)
    try {
      const { data } = await entrarNaTurma(codigo.trim(), 'codigo')
      setSucesso(`Você entrou em ${data.nome}.`)
      setCodigo('')
      await aoEntrar()
    } catch (err) {
      setErro(err.response?.data?.detail || 'Não foi possível entrar na turma.')
    } finally {
      setEntrando(false)
    }
  }

  return (
    <Card>
      <h2 className="titulo-card">Entrar em uma turma</h2>
      <p className="text-xs text-cinza-texto">Use o código de 6 caracteres que o professor passou.</p>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={codigo}
          onChange={e => setCodigo(e.target.value.toUpperCase())}
          placeholder="ABC234"
          maxLength={6}
          className="campo flex-1 font-mono tracking-widest uppercase"
        />
        <Botao type="submit" disabled={entrando || !codigo.trim()}>
          {entrando && <Spinner className="w-4 h-4" />}
          Entrar
        </Botao>
      </form>
      {erro && <p className="text-xs text-erro">{erro}</p>}
      {sucesso && <p className="text-xs text-sucesso">{sucesso}</p>}
    </Card>
  )
}
