import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { Check, ChevronRight, CircleAlert, Minus, Users, X } from 'lucide-react'
import { getExamStudents } from '../api/exam'
import Spinner from '../components/Spinner'
import Card from '../components/ui/Card'
import RotuloSecao from '../components/ui/RotuloSecao'
import Tag from '../components/ui/Tag'

function StatusCell({ status }) {
  if (status.submission_id === null) {
    return (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-botao bg-lavanda text-cinza-texto" aria-label="Não respondeu">
        <Minus className="w-4 h-4" aria-hidden="true" />
      </span>
    )
  }
  if (status.passed) {
    return (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-botao bg-sucesso-fundo text-sucesso" aria-label="Correto">
        <Check className="w-4 h-4" aria-hidden="true" />
      </span>
    )
  }
  if (status.compile_error) {
    return (
      <span className="inline-flex items-center justify-center w-7 h-7 rounded-botao bg-erro-fundo text-erro" title={status.error_category} aria-label="Erro de compilação">
        <X className="w-4 h-4" aria-hidden="true" />
      </span>
    )
  }
  return (
    <span className="inline-flex items-center justify-center w-7 h-7 rounded-botao bg-aviso-fundo text-aviso text-sm font-bold" title={status.error_category} aria-label="Incorreto">
      ~
    </span>
  )
}

export default function StudentsPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getExamStudents(id)
      .then(({ data: d }) => setData(d))
      .catch(() => setError('Erro ao carregar alunos.'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="flex justify-center py-16"><Spinner className="w-6 h-6 text-violeta" /></div>
  if (error) return <p className="text-erro text-sm">{error}</p>

  const totalStudents = data.students.length
  const avgPass = totalStudents > 0
    ? Math.round(data.students.reduce((acc, s) => acc + (s.answered_count > 0 ? s.passed_count / s.answered_count : 0), 0) / totalStudents * 100)
    : 0

  const atRisk = data.students
    .filter(s => s.answered_count > 0 && s.passed_count / s.answered_count < 0.4)
    .sort((a, b) => (a.passed_count / a.answered_count) - (b.passed_count / b.answered_count))

  return (
    <div>
      <div className="flex flex-wrap items-center gap-1 text-sm text-cinza-texto mb-6 lg:hidden">
        <Link to={`/exam/${id}`} className="hover:text-noite">Atividade #{id}</Link>
        <ChevronRight className="w-4 h-4" aria-hidden="true" />
        <span>Alunos</span>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
        <h1 className="titulo-pagina">Alunos</h1>
        <div className="flex gap-4 text-sm text-cinza-texto">
          <span><span className="font-bold text-noite">{totalStudents}</span> alunos</span>
          <span><span className="font-bold text-noite">{avgPass}%</span> acerto médio</span>
        </div>
      </div>

      {atRisk.length > 0 && (
        <div className="mb-6 rounded-card border-2 border-erro bg-erro-fundo p-4">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <CircleAlert className="w-4 h-4 text-erro" aria-hidden="true" />
            <h2 className="titulo-card text-lg! text-erro">Alunos em risco ({atRisk.length})</h2>
            <Tag variante="erro">menos de 40% de acerto</Tag>
          </div>
          <div className="flex flex-wrap gap-2">
            {atRisk.map(s => {
              const pct = Math.round(s.passed_count / s.answered_count * 100)
              return (
                <button
                  key={s.matricula}
                  onClick={() => navigate(`/exam/${id}/students/${encodeURIComponent(s.matricula)}`)}
                  className="inline-flex items-center gap-2 min-h-11 rounded-botao border-2 border-noite bg-white px-3 py-1.5 text-xs hover:bg-lavanda"
                >
                  <span className="font-bold text-noite">{s.matricula}</span>
                  <Tag variante="erro">{s.passed_count}/{s.answered_count} ({pct}%)</Tag>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {totalStudents === 0 ? (
        <Card className="border-dashed border-noite/30! items-center text-center py-16!">
          <Users className="w-10 h-10 text-violeta" aria-hidden="true" />
          <p className="text-sm text-cinza-texto">Nenhuma submissão com matrícula ainda.</p>
        </Card>
      ) : (
        <div className="bg-white rounded-card border-2 border-noite overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-noite bg-lavanda">
                <th className="text-left px-5 py-3 min-w-[180px]"><RotuloSecao as="span">Matrícula</RotuloSecao></th>
                {data.question_numbers.map(num => (
                  <th key={num} className="px-3 py-3 text-center">
                    <RotuloSecao as="span">Q{num}</RotuloSecao>
                  </th>
                ))}
                <th className="px-5 py-3 text-right"><RotuloSecao as="span">Acertos</RotuloSecao></th>
              </tr>
            </thead>
            <tbody className="divide-y-2 divide-noite/10">
              {data.students.map(student => {
                const pct = student.answered_count > 0
                  ? Math.round(student.passed_count / student.answered_count * 100)
                  : null
                return (
                  <tr
                    key={student.matricula}
                    onClick={() => navigate(`/exam/${id}/students/${encodeURIComponent(student.matricula)}`)}
                    className="hover:bg-lavanda cursor-pointer"
                  >
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-botao bg-lavanda flex items-center justify-center shrink-0">
                          <span className="text-xs font-bold text-violeta">
                            {student.matricula?.[0]}
                          </span>
                        </div>
                        <span className="font-bold text-noite truncate max-w-[140px]">{student.matricula}</span>
                      </div>
                    </td>
                    {student.questions.map(qs => (
                      <td key={qs.question_number} className="px-3 py-3 text-center">
                        <StatusCell status={qs} />
                      </td>
                    ))}
                    <td className="px-5 py-3 text-right">
                      <Tag variante={pct === null ? 'neutro' : pct >= 70 ? 'sucesso' : pct >= 40 ? 'aviso' : 'erro'}>
                        {student.passed_count}/{student.answered_count}
                        {pct !== null && ` (${pct}%)`}
                      </Tag>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-cinza-texto">
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-5 rounded-botao bg-sucesso-fundo text-sucesso flex items-center justify-center"><Check className="w-3.5 h-3.5" aria-hidden="true" /></span> Correto
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-5 rounded-botao bg-aviso-fundo text-aviso flex items-center justify-center font-bold">~</span> Incorreto
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-5 rounded-botao bg-erro-fundo text-erro flex items-center justify-center"><X className="w-3.5 h-3.5" aria-hidden="true" /></span> Erro de compilação
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-5 rounded-botao bg-lavanda text-cinza-texto flex items-center justify-center"><Minus className="w-3.5 h-3.5" aria-hidden="true" /></span> Não respondeu
        </span>
      </div>
    </div>
  )
}
