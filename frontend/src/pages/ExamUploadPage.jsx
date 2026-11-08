import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { uploadExam, getTurma } from '../api/exam'
import Spinner from '../components/Spinner'

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
      <div className="flex items-center gap-2 text-sm text-cinza-texto mb-8">
        <Link to="/" className="hover:text-cinza-texto">Turmas</Link>
        <span>›</span>
        <Link to={`/turma/${turmaId}`} className="hover:text-cinza-texto">{turma?.nome ?? `Turma #${turmaId}`}</Link>
        <span>›</span>
        <span className="text-cinza-texto">Nova atividade</span>
      </div>

      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-lavanda rounded-xl mb-4">
          <svg className="w-6 h-6 text-violeta" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold text-noite">Nova atividade</h1>
        <p className="mt-1 text-sm text-cinza-texto">Envie o PDF da prova ou da lista. O Gemini extrai as questões, e depois você escolhe se a atividade é prova ou lista.</p>
      </div>

      <div
        onClick={() => !uploading && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors
          ${dragging ? 'border-violeta bg-lavanda' : 'border-noite/20 bg-white hover:border-violeta/50 hover:bg-lavanda'}
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
            <svg className="mx-auto w-10 h-10 text-cinza-texto/60 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <p className="text-sm font-medium text-cinza-texto">Arraste o arquivo aqui ou <span className="text-violeta">clique para selecionar</span></p>
            <p className="mt-1 text-xs text-cinza-texto">PDF ou DOCX</p>
          </>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-lg bg-erro-fundo border border-erro/30 px-4 py-3 text-sm text-erro">
          {error}
        </div>
      )}
    </div>
  )
}
