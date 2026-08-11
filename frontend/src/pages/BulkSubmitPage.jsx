import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { bulkSubmit, getJob } from '../api/exam'
import Spinner from '../components/Spinner'

const FORMAT_OPTIONS = [
  {
    id: 'by_student',
    label: 'Opção A: por aluno',
    description: 'Pasta = nome do aluno, arquivo = número da questão.',
    example: [
      'respostas.zip',
      '  ├── João Silva/',
      '  │   ├── Q1.c',
      '  │   └── Q2.c',
      '  └── Maria Souza/',
      '      └── Q1.c',
    ],
    hint: 'Compatível com exportação do Moodle e Google Classroom.',
  },
  {
    id: 'by_question',
    label: 'Opção B: por questão',
    description: 'Pasta = número da questão, arquivo = nome do aluno.',
    example: [
      'respostas.zip',
      '  ├── Q1/',
      '  │   ├── joao_silva.c',
      '  │   └── maria_souza.c',
      '  └── Q2/',
      '      └── joao_silva.c',
    ],
    hint: 'Ideal quando o professor organiza os arquivos manualmente por questão.',
  },
]

export default function BulkSubmitPage() {
  const { id } = useParams()
  const inputRef = useRef(null)
  const [format, setFormat] = useState('by_student')
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [job, setJob] = useState(null)     // job de avaliação em segundo plano
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const handleFile = async (file) => {
    if (!file) return
    if (!file.name.endsWith('.zip')) {
      setError('Envie um arquivo .zip.')
      return
    }
    setError('')
    setResult(null)
    setJob(null)
    setUploading(true)
    try {
      const { data } = await bulkSubmit(id, file, format)
      setJob({ id: data.job_id, status: 'pending', processed: 0, total: 0, stage: 'Iniciando…' })
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Erro desconhecido'
      setError(msg)
    } finally {
      setUploading(false)
    }
  }

  // Acompanha o job em background; ao concluir, mostra a tabela de resultados.
  // O usuário pode sair desta página — o indicador global continua o progresso.
  useEffect(() => {
    if (!job || job.status === 'done' || job.status === 'error') return
    const t = setInterval(async () => {
      try {
        const { data } = await getJob(job.id)
        setJob(data)
        if (data.status === 'done') setResult(data.result)
        if (data.status === 'error') setError(data.message || 'Erro ao processar as submissões.')
      } catch { /* silencioso */ }
    }, 1500)
    return () => clearInterval(t)
  }, [job?.id, job?.status]) // eslint-disable-line react-hooks/exhaustive-deps

  const processing = uploading || (job && job.status !== 'done' && job.status !== 'error')

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const selectedFormat = FORMAT_OPTIONS.find(f => f.id === format)

  return (
    <div className="max-w-2xl">
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-6">
        <Link to={`/exam/${id}`} className="hover:text-gray-600">Prova #{id}</Link>
        <span>›</span>
        <span className="text-gray-600">Submissões em lote</span>
      </div>

      <h1 className="text-xl font-semibold text-gray-900 mb-1">Submissões em lote</h1>
      <p className="text-sm text-gray-500 mb-6">
        Faça upload de um ZIP com os códigos dos alunos. Cada arquivo será avaliado e salvo automaticamente.
      </p>

      {/* Seleção de formato */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {FORMAT_OPTIONS.map(opt => (
          <button
            key={opt.id}
            onClick={() => setFormat(opt.id)}
            className={`text-left rounded-xl border p-4 transition-colors ${
              format === opt.id
                ? 'border-purple-400 bg-purple-50 ring-1 ring-purple-400'
                : 'border-gray-200 bg-white hover:border-gray-300'
            }`}
          >
            <p className={`text-sm font-medium mb-1 ${format === opt.id ? 'text-purple-700' : 'text-gray-800'}`}>
              {opt.label}
            </p>
            <p className="text-xs text-gray-500">{opt.description}</p>
          </button>
        ))}
      </div>

      {/* Exemplo da estrutura */}
      <div className="bg-gray-900 rounded-xl p-4 mb-6">
        <p className="text-xs text-gray-400 mb-2 font-medium">Estrutura esperada do ZIP</p>
        <pre className="text-xs font-mono text-green-400 leading-relaxed">
          {selectedFormat.example.join('\n')}
        </pre>
        <p className="text-xs text-gray-500 mt-3">{selectedFormat.hint}</p>
      </div>

      {/* Upload */}
      {!result && !processing && (
        <div
          onClick={() => inputRef.current.click()}
          onDragOver={e => { e.preventDefault(); setDragging(true) }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          className={`
            border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
            ${dragging ? 'border-purple-400 bg-purple-50' : 'border-gray-200 bg-white hover:border-purple-300 hover:bg-gray-50'}
          `}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".zip"
            className="hidden"
            onChange={e => handleFile(e.target.files[0])}
          />
          <svg className="mx-auto w-9 h-9 text-gray-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <p className="text-sm font-medium text-gray-700">
            Arraste o arquivo aqui ou <span className="text-purple-600">clique para selecionar</span>
          </p>
          <p className="mt-1 text-xs text-gray-400">Somente .zip</p>
        </div>
      )}

      {/* Progresso (em segundo plano) */}
      {processing && (
        <div className="bg-white rounded-xl border border-purple-200 p-8 text-center">
          <Spinner className="w-8 h-8 text-purple-600 mx-auto mb-4" />
          <p className="text-sm font-medium text-gray-800 mb-1">
            {uploading ? 'Enviando arquivo…' : (job?.stage || 'Avaliando submissões…')}
          </p>
          <p className="text-xs text-gray-500 mb-4">
            A avaliação roda em segundo plano (Docker por test case). Você pode <strong>sair desta página</strong> e acompanhar pelo indicador de progresso no canto da tela.
          </p>
          {job && job.total > 0 && (
            <>
              <div className="w-full max-w-md mx-auto bg-purple-100 rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-purple-500 transition-all"
                  style={{ width: `${Math.round((job.processed / job.total) * 100)}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-2">{job.processed} / {job.total} arquivos</p>
            </>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Resultado */}
      {result && (
        <div>
          {/* Resumo */}
          <div className="grid grid-cols-3 gap-3 mb-5">
            <div className="bg-white rounded-xl border border-gray-200 p-4 text-center">
              <p className="text-2xl font-semibold text-gray-900">{result.total}</p>
              <p className="text-xs text-gray-400 mt-0.5">Arquivos</p>
            </div>
            <div className="bg-green-50 rounded-xl border border-green-200 p-4 text-center">
              <p className="text-2xl font-semibold text-green-700">{result.processed}</p>
              <p className="text-xs text-green-600 mt-0.5">Processados</p>
            </div>
            <div className={`rounded-xl border p-4 text-center ${result.errors > 0 ? 'bg-red-50 border-red-200' : 'bg-gray-50 border-gray-200'}`}>
              <p className={`text-2xl font-semibold ${result.errors > 0 ? 'text-red-600' : 'text-gray-400'}`}>{result.errors}</p>
              <p className={`text-xs mt-0.5 ${result.errors > 0 ? 'text-red-500' : 'text-gray-400'}`}>Erros</p>
            </div>
          </div>

          {/* Tabela de itens */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-5">
            <div className="grid grid-cols-[1fr_80px_80px_1fr] gap-0 px-4 py-2 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500">
              <span>Aluno</span>
              <span>Questão</span>
              <span>Status</span>
              <span>Observação</span>
            </div>
            <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
              {result.items.map((item, i) => (
                <div key={i} className="grid grid-cols-[1fr_80px_80px_1fr] gap-0 px-4 py-2.5 items-center">
                  <span className="text-sm text-gray-800 truncate">{item.matricula || '—'}</span>
                  <span className="text-sm text-gray-600">{item.question ? `Q${item.question}` : '—'}</span>
                  <span>
                    {item.status === 'ok'
                      ? <span className="text-xs font-medium text-green-700 bg-green-50 border border-green-200 px-2 py-0.5 rounded-md">OK</span>
                      : <span className="text-xs font-medium text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded-md">Erro</span>
                    }
                  </span>
                  <span className="text-xs text-gray-500 truncate">{item.message || item.file}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => { setResult(null); setError(''); setJob(null) }}
              className="text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 transition-colors"
            >
              Enviar outro ZIP
            </button>
            <Link
              to={`/exam/${id}`}
              className="text-sm px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Voltar à prova
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
