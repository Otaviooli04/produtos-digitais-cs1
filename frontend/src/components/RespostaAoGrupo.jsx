import { useState } from 'react'
import Spinner from './Spinner'
import Botao from './ui/Botao'

/**
 * O professor escreve uma vez e o texto chega a todo mundo que errou do mesmo
 * jeito. É o passo que fecha o ciclo do agrupamento: sem ele o professor vê a
 * turma organizada e continua respondendo aluno por aluno fora do sistema.
 *
 * O insight do Gemini é oferecido como rascunho, nunca como resposta pronta.
 * Quem responde é o professor.
 */
export default function RespostaAoGrupo({ resposta, respostaEm, insight, alunos, onSave }) {
  const [aberto, setAberto] = useState(false)
  const [texto, setTexto] = useState(resposta || '')
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')

  const salvar = async () => {
    setErro('')
    setSalvando(true)
    try {
      await onSave(texto.trim())
      setAberto(false)
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível salvar a resposta.')
    } finally {
      setSalvando(false)
    }
  }

  const cancelar = () => {
    setTexto(resposta || '')
    setErro('')
    setAberto(false)
  }

  if (!aberto) {
    return (
      <div className="mt-3 pt-3 border-t-2 border-noite/10">
        {resposta ? (
          <div className="flex gap-2">
            <div className="w-1 bg-sucesso rounded-full shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-xs font-bold text-sucesso mb-0.5">
                Seu retorno para este grupo
                {respostaEm && <span className="font-normal text-cinza-texto"> · enviado</span>}
              </p>
              <p className="text-sm text-cinza-texto leading-relaxed whitespace-pre-wrap break-words">{resposta}</p>
              <button
                onClick={() => setAberto(true)}
                className="mt-1.5 min-h-11 text-xs font-bold text-cinza-texto hover:text-noite transition-colors"
              >
                Editar
              </button>
            </div>
          </div>
        ) : (
          <Botao variante="secundario" onClick={() => setAberto(true)} className="min-h-9! px-3.5! text-[13px]!">
            Responder ao grupo
            {alunos > 0 && <span className="font-normal text-cinza-texto"> · {alunos} aluno{alunos !== 1 ? 's' : ''}</span>}
          </Botao>
        )}
      </div>
    )
  }

  return (
    <div className="mt-3 pt-3 border-t-2 border-noite/10">
      <p className="text-xs text-cinza-texto mb-1.5">
        O que você escrever aqui chega a todo aluno deste grupo, na tentativa mais
        recente dele. Diga o que retomar, não a solução.
      </p>
      <textarea
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        rows={4}
        autoFocus
        placeholder="Ex.: vale rever a condição de parada do laço antes de enviar de novo."
        className="campo"
      />
      {insight && texto !== insight && (
        <button
          onClick={() => setTexto(insight)}
          className="mt-1.5 min-h-11 text-xs font-bold text-violeta hover:text-violeta-escuro hover:underline transition-colors"
        >
          Usar a descrição do Gemini como ponto de partida
        </button>
      )}
      {erro && <p className="mt-1.5 text-xs text-erro">{erro}</p>}
      <div className="flex items-center gap-2 mt-2">
        <Botao onClick={salvar} disabled={salvando} className="min-h-9! px-3.5! text-[13px]!">
          {salvando && <Spinner className="w-3 h-3" />}
          {texto.trim() ? 'Enviar ao grupo' : 'Apagar resposta'}
        </Botao>
        <Botao variante="secundario" onClick={cancelar} disabled={salvando} className="min-h-9! px-3.5! text-[13px]!">
          Cancelar
        </Botao>
      </div>
    </div>
  )
}
