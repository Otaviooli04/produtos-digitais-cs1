import { useState } from 'react'
import Spinner from './Spinner'
import { inputLocalParaIso, isoParaInputLocal } from '../utils/atividade'

/**
 * Define o que a atividade é para o aluno. Treino é para estudar durante o
 * semestre; prova respeita a janela e o teto de tentativas. Janela e teto valem
 * sempre que preenchidos, em qualquer um dos dois modos.
 */
export default function DisponibilidadeCard({ exam, onSave }) {
  const [aberto, setAberto] = useState(false)
  const [modo, setModo] = useState(exam.modo || 'prova')
  const [abreEm, setAbreEm] = useState(isoParaInputLocal(exam.abre_em))
  const [fechaEm, setFechaEm] = useState(isoParaInputLocal(exam.fecha_em))
  const [maxTentativas, setMaxTentativas] = useState(
    exam.max_tentativas != null ? String(exam.max_tentativas) : '')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')

  const salvar = async () => {
    setErro('')
    setSalvando(true)
    const limpar = []
    if (!abreEm) limpar.push('abre_em')
    if (!fechaEm) limpar.push('fecha_em')
    if (!maxTentativas.trim()) limpar.push('max_tentativas')
    try {
      await onSave({
        modo,
        abre_em: inputLocalParaIso(abreEm),
        fecha_em: inputLocalParaIso(fechaEm),
        max_tentativas: maxTentativas.trim() ? Number(maxTentativas) : null,
        limpar,
      })
      setAberto(false)
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível salvar.')
    } finally {
      setSalvando(false)
    }
  }

  const campo = 'w-full text-sm rounded-lg border border-noite/20 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-violeta focus:border-transparent'

  const resumo = [
    exam.modo === 'treino' ? 'Lista' : 'Prova',
    exam.abre_em || exam.fecha_em ? 'com janela' : 'sem janela',
    exam.max_tentativas != null ? `até ${exam.max_tentativas} tentativas` : 'tentativas ilimitadas',
  ].join(' · ')

  return (
    <div className="mb-5 rounded-xl border border-noite/20 bg-white px-5 py-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-noite">Disponibilidade para o aluno</p>
          <p className="text-xs text-cinza-texto mt-0.5">{resumo}</p>
        </div>
        <button
          onClick={() => setAberto(a => !a)}
          className="text-sm px-3 py-1.5 rounded-lg border border-noite/20 text-cinza-texto hover:bg-lavanda transition-colors"
        >
          {aberto ? 'Fechar' : 'Configurar'}
        </button>
      </div>

      {aberto && (
        <div className="mt-4 space-y-4 border-t border-noite/10 pt-4">
          <div>
            <label className="block text-xs font-medium text-cinza-texto mb-1.5">Modo</label>
            <div className="flex gap-2">
              {[['treino', 'Lista'], ['prova', 'Prova']].map(([valor, rotulo]) => (
                <button
                  key={valor}
                  onClick={() => setModo(valor)}
                  className={`text-sm px-4 py-1.5 rounded-lg border transition-colors ${
                    modo === valor
                      ? 'bg-violeta text-white border-violeta'
                      : 'border-noite/20 text-cinza-texto hover:bg-lavanda'
                  }`}
                >
                  {rotulo}
                </button>
              ))}
            </div>
            <p className="mt-1.5 text-xs text-cinza-texto">
              {modo === 'treino'
                ? 'O aluno pratica quando quiser e vê o diagnóstico de cada tentativa.'
                : 'Use a janela e o teto de tentativas abaixo para controlar a avaliação.'}
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className="block text-xs font-medium text-cinza-texto mb-1.5">Abre em</label>
              <input type="datetime-local" value={abreEm} onChange={e => setAbreEm(e.target.value)} className={campo} />
            </div>
            <div>
              <label className="block text-xs font-medium text-cinza-texto mb-1.5">Fecha em</label>
              <input type="datetime-local" value={fechaEm} onChange={e => setFechaEm(e.target.value)} className={campo} />
            </div>
            <div>
              <label className="block text-xs font-medium text-cinza-texto mb-1.5">Tentativas por questão</label>
              <input
                type="number"
                min="1"
                value={maxTentativas}
                onChange={e => setMaxTentativas(e.target.value)}
                placeholder="ilimitadas"
                className={campo}
              />
            </div>
          </div>

          {erro && <p className="text-xs text-erro">{erro}</p>}

          <button
            onClick={salvar}
            disabled={salvando}
            className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-violeta text-white hover:bg-violeta-escuro disabled:opacity-40 transition-colors"
          >
            {salvando && <Spinner className="w-4 h-4" />}
            Salvar
          </button>
        </div>
      )}
    </div>
  )
}
