import { useState } from 'react'
import Spinner from './Spinner'
import Botao from './ui/Botao'
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
          className={`rounded-botao px-4 py-2.5 border-2 border-violeta ${i === 0 ? 'bg-lavanda' : 'bg-white'}`}
        >
          <p className="text-xs font-bold text-violeta mb-0.5">{i === 0 ? 'Dica' : 'Outra pista'}</p>
          <p className="text-xs text-violeta whitespace-pre-wrap break-words">{pista}</p>
        </div>
      ))}

      {explicacao && (
        <div className="rounded-botao bg-lavanda border-2 border-violeta px-4 py-2.5">
          <p className="text-xs font-bold text-violeta mb-0.5">Explicando o seu código</p>
          <p className="text-xs text-violeta whitespace-pre-wrap break-words">{explicacao}</p>
        </div>
      )}

      {nivel < 3 && (
        <div>
          <Botao variante="secundario" onClick={abrirProxima} disabled={carregando}>
            {carregando && <Spinner className="w-3.5 h-3.5" />}
            {carregando ? 'Pensando…' : PROXIMO[nivel]}
          </Botao>
          {erro && <p className="mt-1.5 text-xs text-erro">{erro}</p>}
        </div>
      )}
    </div>
  )
}
