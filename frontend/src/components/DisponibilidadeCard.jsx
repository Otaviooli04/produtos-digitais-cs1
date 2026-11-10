import { useState } from 'react'
import Spinner from './Spinner'
import Botao from './ui/Botao'
import Card from './ui/Card'
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

  const resumo = [
    exam.modo === 'treino' ? 'Lista' : 'Prova',
    exam.abre_em || exam.fecha_em ? 'com janela' : 'sem janela',
    exam.max_tentativas != null ? `até ${exam.max_tentativas} tentativas` : 'tentativas ilimitadas',
  ].join(' · ')

  return (
    <Card className="py-4!">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-bold text-noite">Disponibilidade para o aluno</p>
          <p className="text-xs text-cinza-texto mt-0.5">{resumo}</p>
        </div>
        <Botao variante="secundario" onClick={() => setAberto(a => !a)}>
          {aberto ? 'Fechar' : 'Configurar'}
        </Botao>
      </div>

      {aberto && (
        <div className="space-y-4 border-t-2 border-noite/10 pt-4">
          <div>
            <label className="block text-xs font-bold text-cinza-texto mb-1.5">Modo</label>
            <div className="flex gap-2">
              {[['treino', 'Lista'], ['prova', 'Prova']].map(([valor, rotulo]) => (
                <Botao
                  key={valor}
                  variante={modo === valor ? 'primario' : 'secundario'}
                  onClick={() => setModo(valor)}
                  aria-pressed={modo === valor}
                >
                  {rotulo}
                </Botao>
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
              <label className="block text-xs font-bold text-cinza-texto mb-1.5">Abre em</label>
              <input type="datetime-local" value={abreEm} onChange={e => setAbreEm(e.target.value)} className="campo" />
            </div>
            <div>
              <label className="block text-xs font-bold text-cinza-texto mb-1.5">Fecha em</label>
              <input type="datetime-local" value={fechaEm} onChange={e => setFechaEm(e.target.value)} className="campo" />
            </div>
            <div>
              <label className="block text-xs font-bold text-cinza-texto mb-1.5">Tentativas por questão</label>
              <input
                type="number"
                min="1"
                value={maxTentativas}
                onChange={e => setMaxTentativas(e.target.value)}
                placeholder="ilimitadas"
                className="campo"
              />
            </div>
          </div>

          {erro && <p className="text-xs text-erro">{erro}</p>}

          <div>
            <Botao onClick={salvar} disabled={salvando}>
              {salvando && <Spinner className="w-4 h-4" />}
              Salvar
            </Botao>
          </div>
        </div>
      )}
    </Card>
  )
}
