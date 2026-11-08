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
      <div className="flex items-center gap-2 text-sm text-cinza-texto mb-6">
        <Link to={`/exam/${id}`} className="hover:text-cinza-texto">Atividade #{id}</Link>
        <span>›</span>
        <span className="text-cinza-texto">Submissões em lote</span>
      </div>

      <h1 className="text-xl font-semibold text-noite mb-1">Submissões em lote</h1>
      <p className="text-sm text-cinza-texto mb-6">
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
                ? 'border-violeta bg-lavanda ring-1 ring-violeta'
                : 'border-noite/20 bg-white hover:border-noite/30'
            }`}
          >
            <p className={`text-sm font-medium mb-1 ${format === opt.id ? 'text-violeta' : 'text-noite'}`}>
              {opt.label}
            </p>
            <p className="text-xs text-cinza-texto">{opt.description}</p>
          </button>
        ))}
      </div>

      {/* Exemplo da estrutura */}
      <div className="bg-noite rounded-xl p-4 mb-6">
        <p className="text-xs text-white/60 mb-2 font-medium">Estrutura esperada do ZIP</p>
        <pre className="text-xs font-mono text-codigo-sucesso leading-relaxed">
          {selectedFormat.example.join('\n')}
        </pre>
        <p className="text-xs text-white/60 mt-3">{selectedFormat.hint}</p>
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
            ${dragging ? 'border-violeta bg-lavanda' : 'border-noite/20 bg-white hover:border-violeta/50 hover:bg-lavanda'}
          `}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".zip"
            className="hidden"
            onChange={e => handleFile(e.target.files[0])}
          />
          <svg className="mx-auto w-9 h-9 text-cinza-texto/60 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
          <p className="text-sm font-medium text-cinza-texto">
            Arraste o arquivo aqui ou <span className="text-violeta">clique para selecionar</span>
          </p>
          <p className="mt-1 text-xs text-cinza-texto">Somente .zip</p>
        </div>
      )}

      {/* Progresso (em segundo plano) */}
      {processing && (
        <div className="bg-white rounded-xl border border-violeta/30 p-8 text-center">
          <Spinner className="w-8 h-8 text-violeta mx-auto mb-4" />
          <p className="text-sm font-medium text-noite mb-1">
            {uploading ? 'Enviando arquivo…' : (job?.stage || 'Avaliando submissões…')}
          </p>
          <p className="text-xs text-cinza-texto mb-4">
            A avaliação roda em segundo plano (Docker por test case). Você pode <strong>sair desta página</strong> e acompanhar pelo indicador de progresso no canto da tela.
          </p>
          {job && job.total > 0 && (
            <>
              <div className="w-full max-w-md mx-auto bg-lavanda rounded-full h-2">
                <div
                  className="h-2 rounded-full bg-violeta transition-all"
                  style={{ width: `${Math.round((job.processed / job.total) * 100)}%` }}
                />
              </div>
              <p className="text-xs text-cinza-texto mt-2">{job.processed} / {job.total} arquivos</p>
            </>
          )}
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg bg-erro-fundo border border-erro/30 px-4 py-3 text-sm text-erro">
          {error}
        </div>
      )}

      {/* Resultado */}
      {result && (
        <div>
          {/* Resumo */}
          <div className="grid grid-cols-3 gap-3 mb-5">
            <div className="bg-white rounded-xl border border-noite/20 p-4 text-center">
              <p className="text-2xl font-semibold text-noite">{result.total}</p>
              <p className="text-xs text-cinza-texto mt-0.5">Arquivos</p>
            </div>
            <div className="bg-sucesso-fundo rounded-xl border border-sucesso/30 p-4 text-center">
              <p className="text-2xl font-semibold text-sucesso">{result.processed}</p>
              <p className="text-xs text-sucesso mt-0.5">Processados</p>
            </div>
            <div className={`rounded-xl border p-4 text-center ${result.errors > 0 ? 'bg-erro-fundo border-erro/30' : 'bg-lavanda border-noite/20'}`}>
              <p className={`text-2xl font-semibold ${result.errors > 0 ? 'text-erro' : 'text-cinza-texto'}`}>{result.errors}</p>
              <p className={`text-xs mt-0.5 ${result.errors > 0 ? 'text-erro' : 'text-cinza-texto'}`}>Erros</p>
            </div>
          </div>

          {/* Tabela de itens */}
          <div className="bg-white rounded-xl border border-noite/20 overflow-hidden mb-5">
            <div className="grid grid-cols-[1fr_80px_80px_1fr] gap-0 px-4 py-2 bg-lavanda border-b border-noite/20 text-xs font-medium text-cinza-texto">
              <span>Aluno</span>
              <span>Questão</span>
              <span>Status</span>
              <span>Observação</span>
            </div>
            <div className="divide-y divide-noite/10 max-h-96 overflow-y-auto">
              {result.items.map((item, i) => (
                <div key={i} className="grid grid-cols-[1fr_80px_80px_1fr] gap-0 px-4 py-2.5 items-center">
                  <span className="text-sm text-noite truncate">{item.matricula || '—'}</span>
                  <span className="text-sm text-cinza-texto">{item.question ? `Q${item.question}` : '—'}</span>
                  <span>
                    {item.status === 'ok'
                      ? <span className="text-xs font-medium text-sucesso bg-sucesso-fundo border border-sucesso/30 px-2 py-0.5 rounded-md">OK</span>
                      : <span className="text-xs font-medium text-erro bg-erro-fundo border border-erro/30 px-2 py-0.5 rounded-md">Erro</span>
                    }
                  </span>
                  <span className="text-xs text-cinza-texto truncate">{item.message || item.file}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => { setResult(null); setError(''); setJob(null) }}
              className="text-sm px-4 py-2 rounded-lg bg-violeta text-white hover:bg-violeta-escuro transition-colors"
            >
              Enviar outro ZIP
            </button>
            <Link
              to={`/exam/${id}`}
              className="text-sm px-4 py-2 rounded-lg border border-noite/20 text-cinza-texto hover:bg-lavanda transition-colors"
            >
              Voltar à atividade
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}
