import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { getActiveJobs } from '../api/exam'
import Spinner from './Spinner'

const KIND_LABEL = {
  exam_upload: 'Extraindo prova (Gemini)',
  bulk_submit: 'Avaliando submissões',
}

// Indicador global de processamento: aparece no canto enquanto há tarefas em
// segundo plano (extração via Gemini, avaliação em lote), para o usuário
// acompanhar o progresso enquanto navega livremente pelo sistema.
export default function JobDock() {
  const [jobs, setJobs] = useState([])
  const [justFinished, setJustFinished] = useState(false)
  const prevCount = useRef(0)

  useEffect(() => {
    let alive = true
    const tick = async () => {
      try {
        const { data } = await getActiveJobs()
        if (!alive) return
        if (data.length === 0 && prevCount.current > 0) {
          setJustFinished(true)
          setTimeout(() => alive && setJustFinished(false), 4000)
        }
        prevCount.current = data.length
        setJobs(data)
      } catch { /* não logado / sem rede: silencioso */ }
    }
    tick()
    const t = setInterval(tick, 2500)
    return () => { alive = false; clearInterval(t) }
  }, [])

  if (jobs.length === 0 && !justFinished) return null

  return (
    <div className="fixed bottom-5 right-5 z-40 w-80 space-y-2">
      {jobs.map(job => {
        const pct = job.total > 0 ? Math.round((job.processed / job.total) * 100) : null
        return (
          <div key={job.id} className="bg-white rounded-xl border border-purple-200 shadow-lg p-4">
            <div className="flex items-center gap-2.5 mb-1.5">
              <Spinner className="w-4 h-4 text-purple-600 shrink-0" />
              <p className="text-sm font-medium text-gray-800 flex-1 truncate">
                {KIND_LABEL[job.kind] || 'Processando'}
              </p>
              {pct !== null && <span className="text-xs text-gray-400">{pct}%</span>}
            </div>
            <p className="text-xs text-gray-500 truncate">{job.stage || 'Em andamento…'}</p>
            {pct !== null && (
              <div className="mt-2 w-full bg-gray-100 rounded-full h-1.5">
                <div className="h-1.5 rounded-full bg-purple-500 transition-all" style={{ width: `${pct}%` }} />
              </div>
            )}
            {job.exam_id && (
              <Link
                to={`/exam/${job.exam_id}`}
                className="mt-2 inline-block text-xs text-purple-600 hover:underline"
              >
                Abrir prova →
              </Link>
            )}
          </div>
        )
      })}

      {jobs.length === 0 && justFinished && (
        <div className="bg-white rounded-xl border border-green-200 shadow-lg p-4 flex items-center gap-2.5">
          <svg className="w-5 h-5 text-green-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <p className="text-sm font-medium text-gray-800">Processamento concluído</p>
        </div>
      )}
    </div>
  )
}
