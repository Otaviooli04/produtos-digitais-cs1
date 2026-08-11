import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { uploadExam } from '../api/exam'
import Spinner from '../components/Spinner'

export default function UploadPage() {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)
  const navigate = useNavigate()

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
      const { data } = await uploadExam(file)
      // Extração das questões roda em segundo plano; o dashboard mostra o progresso.
      navigate(`/exam/${data.exam_id}`)
    } catch (e) {
      setError(e.response?.data?.detail || 'Erro ao processar a prova. Tente novamente.')
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
    <div className="max-w-xl mx-auto mt-16">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 bg-purple-100 rounded-xl mb-4">
          <svg className="w-6 h-6 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold text-gray-900">Nova prova</h1>
        <p className="mt-1 text-sm text-gray-500">Faça upload do arquivo da prova. O Gemini irá extrair as questões automaticamente.</p>
      </div>

      <div
        onClick={() => !uploading && inputRef.current.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`
          border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors
          ${dragging ? 'border-purple-400 bg-purple-50' : 'border-gray-200 bg-white hover:border-purple-300 hover:bg-gray-50'}
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
            <Spinner className="w-8 h-8 text-purple-600" />
            <p className="text-sm text-gray-500">Enviando arquivo…</p>
          </div>
        ) : (
          <>
            <svg className="mx-auto w-10 h-10 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
            </svg>
            <p className="text-sm font-medium text-gray-700">Arraste o arquivo aqui ou <span className="text-purple-600">clique para selecionar</span></p>
            <p className="mt-1 text-xs text-gray-400">PDF ou DOCX</p>
          </>
        )}
      </div>

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  )
}
