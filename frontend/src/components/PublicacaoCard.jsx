import { useState } from 'react'
import Spinner from './Spinner'

/**
 * O portão entre a atividade montada e a atividade visível para o aluno.
 * Enquanto é rascunho ela não existe do lado de lá, o que dá ao professor o
 * tempo de revisar o que o extrator produziu. Publicar exige questão com caso
 * de teste, senão o aluno recebe uma questão que ninguém consegue resolver.
 */
export default function PublicacaoCard({ exam, onSave }) {
  const [salvando, setSalvando] = useState(false)
  const [erro, setErro] = useState('')

  const publicada = !!exam.publicada
  const impedimentos = exam.impedimentos || []
  const podePublicar = !!exam.pode_publicar

  const alternar = async () => {
    setErro('')
    setSalvando(true)
    try {
      await onSave({ publicada: !publicada })
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível salvar.')
    } finally {
      setSalvando(false)
    }
  }

  return (
    <div
      className={`mb-5 rounded-xl border px-5 py-4 ${
        publicada ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-3">
        <div className="min-w-0">
          <p className={`text-sm font-medium ${publicada ? 'text-green-900' : 'text-amber-900'}`}>
            {publicada ? 'Publicada para a turma' : 'Rascunho, invisível para o aluno'}
          </p>
          <p className={`text-xs mt-0.5 ${publicada ? 'text-green-700' : 'text-amber-700'}`}>
            {publicada
              ? 'Os alunos da turma veem esta atividade na lista deles.'
              : 'Revise as questões e os casos de teste antes de publicar.'}
          </p>
          {!publicada && impedimentos.length > 0 && (
            <ul className="mt-2 text-xs text-amber-800 list-disc list-inside">
              {impedimentos.map((motivo, i) => <li key={i}>{motivo}</li>)}
            </ul>
          )}
          {erro && <p className="mt-2 text-xs text-red-600">{erro}</p>}
        </div>

        <button
          onClick={alternar}
          disabled={salvando || (!publicada && !podePublicar)}
          className={`inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
            publicada
              ? 'border border-gray-200 bg-white text-gray-700 hover:bg-gray-50'
              : 'bg-green-600 text-white hover:bg-green-700'
          }`}
        >
          {salvando && <Spinner className="w-3.5 h-3.5" />}
          {publicada ? 'Voltar para rascunho' : 'Publicar para a turma'}
        </button>
      </div>
    </div>
  )
}
