import { useState } from 'react'
import Spinner from './Spinner'
import Botao from './ui/Botao'
import Card from './ui/Card'

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
    <Card
      className={`py-4! gap-0! ${
        publicada ? 'border-sucesso! bg-sucesso-fundo!' : 'border-aviso! bg-aviso-fundo!'
      }`}
    >
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-3">
        <div className="min-w-0">
          <p className={`text-sm font-bold ${publicada ? 'text-sucesso' : 'text-aviso'}`}>
            {publicada ? 'Publicada para a turma' : 'Rascunho, invisível para o aluno'}
          </p>
          <p className={`text-xs mt-0.5 ${publicada ? 'text-sucesso' : 'text-aviso'}`}>
            {publicada
              ? 'Os alunos da turma veem esta atividade na lista deles.'
              : 'Revise as questões e os casos de teste antes de publicar.'}
          </p>
          {!publicada && impedimentos.length > 0 && (
            <ul className="mt-2 text-xs text-aviso list-disc list-inside">
              {impedimentos.map((motivo, i) => <li key={i}>{motivo}</li>)}
            </ul>
          )}
          {erro && <p className="mt-2 text-xs text-erro">{erro}</p>}
        </div>

        <Botao
          variante={publicada ? 'secundario' : 'primario'}
          onClick={alternar}
          disabled={salvando || (!publicada && !podePublicar)}
        >
          {salvando && <Spinner className="w-3.5 h-3.5" />}
          {publicada ? 'Voltar para rascunho' : 'Publicar para a turma'}
        </Botao>
      </div>
    </Card>
  )
}
