import { useState } from 'react'
import Spinner from './Spinner'
import { pedirAjuda } from '../api/aluno'

const PROXIMO = ['Preciso de uma dica', 'Outra pista', 'Ver explicação completa']

/**
 * Ajuda da tentativa errada em etapas (2.3): pista geral, pista que aponta a
 * parte do código e explicação completa, uma de cada vez. O servidor só devolve
 * até a etapa pedida e guarda até onde o aluno foi, que é o dado do experimento.
 */
export default function AjudaEmEtapas({ tentativa }) {
  const [pistas, setPistas] = useState(tentativa.pistas || [])
  const [explicacao, setExplicacao] = useState(tentativa.explicacao || null)
  const [nivel, setNivel] = useState(tentativa.nivel_de_ajuda || 0)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState('')

  if (tentativa.ajuda_bloqueada) {
    return (
      <p className="mt-3 text-xs text-cinza-texto">A dica fica disponível quando a prova fechar.</p>
    )
  }

  const abrirProxima = async () => {
    setErro('')
    setCarregando(true)
    try {
      const { data } = await pedirAjuda(tentativa.submission_id, nivel + 1)
      setPistas(data.pistas)
      setExplicacao(data.explicacao)
      setNivel(data.nivel)
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível gerar a dica agora. Tente de novo.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="mt-3 space-y-2">
      {pistas.map((pista, i) => (
        <div
          key={i}
          className={`rounded-lg px-4 py-2.5 border ${i === 0 ? 'bg-lavanda border-violeta/30' : 'bg-white border-violeta/15'}`}
        >
          <p className="text-xs font-medium text-violeta mb-0.5">{i === 0 ? 'Dica' : 'Outra pista'}</p>
          <p className="text-xs text-violeta whitespace-pre-wrap break-words">{pista}</p>
        </div>
      ))}

      {explicacao && (
        <div className="rounded-lg bg-lavanda border border-violeta/15 px-4 py-2.5">
          <p className="text-xs font-medium text-violeta mb-0.5">Explicando o seu código</p>
          <p className="text-xs text-violeta whitespace-pre-wrap break-words">{explicacao}</p>
        </div>
      )}

      {nivel < 3 && (
        <div>
          <button
            onClick={abrirProxima}
            disabled={carregando}
            className="inline-flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg border border-violeta/30 text-violeta hover:bg-lavanda disabled:opacity-40 transition-colors"
          >
            {carregando && <Spinner className="w-3.5 h-3.5" />}
            {carregando ? 'Pensando…' : PROXIMO[nivel]}
          </button>
          {erro && <p className="mt-1.5 text-xs text-erro">{erro}</p>}
        </div>
      )}
    </div>
  )
}
