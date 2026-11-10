import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { uploadExam, getTurma } from '../api/exam'
import { ChevronRight, FileText, Upload } from 'lucide-react'
import Spinner from '../components/Spinner'
import Card from '../components/ui/Card'

export default function ExamUploadPage() {
  const { turmaId } = useParams()
  const navigate = useNavigate()
  const [turma, setTurma] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    getTurma(turmaId).then(({ data }) => setTurma(data)).catch(() => {})
  }, [turmaId])

  const handleFile = async (file) => {
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      setError('Formato inválido. Envie PDF ou DOCX.')
      return
    }
    setError('')
    setUploading(true)
    try {
      const { data } = await uploadExam(file, turmaId)
      // A extração das questões roda em segundo plano; o dashboard exibe o progresso.
      navigate(`/exam/${data.exam_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao processar o arquivo. Tente novamente.')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="max-w-xl mx-auto mt-8">
      <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto mb-8 lg:hidden">
        <Link to="/" className="hover:text-noite">Turmas</Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <Link to={`/turma/${turmaId}?secao=atividades`} className="hover:text-noite">{turma?.nome ?? `Turma #${turmaId}`}</Link>
      </div>

      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-lavanda rounded-botao mb-4">
          <FileText className="w-6 h-6 text-violeta" aria-hidden="true" />
        </div>
        <h1 className="titulo-pagina">Nova atividade</h1>
        <p className="mt-1 text-sm text-cinza-texto">Envie o PDF da prova ou da lista. O Gemini extrai as questões, e depois você escolhe se a atividade é prova ou lista.</p>
      </div>

      <Card
        onClick={() => !uploading && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`
          border-dashed border-noite/30! p-12! text-center cursor-pointer transition-colors
          ${dragging ? 'bg-lavanda!' : 'hover:bg-lavanda'}
          ${uploading ? 'pointer-events-none opacity-60' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.doc"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />

        {uploading ? (
          <div className="flex flex-col items-center gap-3">
            <Spinner className="w-8 h-8 text-violeta" />
            <p className="text-sm text-cinza-texto">Enviando arquivo…</p>
          </div>
        ) : (
          <>
            <Upload className="mx-auto w-10 h-10 text-violeta mb-3" aria-hidden="true" />
            <p className="text-sm font-bold text-noite">Arraste o arquivo aqui ou <span className="text-violeta">clique para selecionar</span></p>
            <p className="mt-1 text-xs text-cinza-texto">PDF ou DOCX</p>
          </>
        )}
      </Card>

      {error && (
        <div className="mt-4 rounded-botao bg-erro-fundo border-2 border-erro px-4 py-3 text-sm text-erro">
          {error}
        </div>
      )}
    </div>
  )
}
