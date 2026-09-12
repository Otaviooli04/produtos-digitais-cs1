import { useState } from 'react'
import Spinner from './Spinner'

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
      <div className="mt-3 pt-3 border-t border-gray-100">
        {resposta ? (
          <div className="flex gap-2">
            <div className="w-0.5 bg-green-300 rounded-full shrink-0" />
            <div className="min-w-0 flex-1">
              <p className="text-xs font-medium text-green-700 mb-0.5">
                Seu retorno para este grupo
                {respostaEm && <span className="font-normal text-gray-400"> · enviado</span>}
              </p>
              <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{resposta}</p>
              <button
                onClick={() => setAberto(true)}
                className="mt-1.5 text-xs text-gray-400 hover:text-gray-600 transition-colors"
              >
                Editar
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setAberto(true)}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
          >
            Responder ao grupo
            {alunos > 0 && <span className="text-gray-400"> · {alunos} aluno{alunos !== 1 ? 's' : ''}</span>}
          </button>
        )}
      </div>
    )
  }

  return (
    <div className="mt-3 pt-3 border-t border-gray-100">
      <p className="text-xs text-gray-500 mb-1.5">
        O que você escrever aqui chega a todo aluno deste grupo, na tentativa mais
        recente dele. Diga o que retomar, não a solução.
      </p>
      <textarea
        value={texto}
        onChange={(e) => setTexto(e.target.value)}
        rows={4}
        autoFocus
        placeholder="Ex.: vale rever a condição de parada do laço antes de enviar de novo."
        className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-300"
      />
      {insight && texto !== insight && (
        <button
          onClick={() => setTexto(insight)}
          className="mt-1.5 text-xs text-purple-600 hover:text-purple-700 transition-colors"
        >
          Usar a descrição do Gemini como ponto de partida
        </button>
      )}
      {erro && <p className="mt-1.5 text-xs text-red-600">{erro}</p>}
      <div className="flex items-center gap-2 mt-2">
        <button
          onClick={salvar}
          disabled={salvando}
          className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors"
        >
          {salvando && <Spinner className="w-3 h-3" />}
          {texto.trim() ? 'Enviar ao grupo' : 'Apagar resposta'}
        </button>
        <button
          onClick={cancelar}
          disabled={salvando}
          className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors"
        >
          Cancelar
        </button>
      </div>
    </div>
  )
}
