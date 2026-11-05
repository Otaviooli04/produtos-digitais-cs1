import { useState } from 'react'
import { entrarNaTurma } from '../api/aluno'
import Spinner from './Spinner'

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
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h2 className="text-sm font-semibold text-gray-900 mb-1">Entrar em uma turma</h2>
      <p className="text-xs text-gray-400 mb-4">Use o código de 6 caracteres que o professor passou.</p>
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={codigo}
          onChange={e => setCodigo(e.target.value.toUpperCase())}
          placeholder="ABC234"
          maxLength={6}
          className="flex-1 text-sm font-mono tracking-widest uppercase rounded-lg border border-gray-200 px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
        <button
          type="submit"
          disabled={entrando || !codigo.trim()}
          className="inline-flex items-center justify-center gap-2 text-sm px-5 py-2.5 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {entrando && <Spinner className="w-4 h-4" />}
          Entrar
        </button>
      </form>
      {erro && <p className="mt-2 text-xs text-red-600">{erro}</p>}
      {sucesso && <p className="mt-2 text-xs text-green-600">{sucesso}</p>}
    </div>
  )
}
