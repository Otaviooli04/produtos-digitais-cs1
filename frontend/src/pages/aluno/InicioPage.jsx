import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { gerarExercicio, getInicio } from '../../api/aluno'
import EntrarNaTurma from '../../components/EntrarNaTurma'
import Spinner from '../../components/Spinner'
import { modoLabel } from '../../utils/atividade'
import { prazoRelativo } from '../../utils/datas'
import { shortError } from '../../utils/errorLabels'

const TEXTO_DA_NOVIDADE = {
  retorno: 'Seu professor respondeu ao seu erro',
  exercicio: 'Exercício novo pronto na trilha',
}

function linkDaNovidade(n) {
  return n.tipo === 'retorno'
    ? `/aluno/atividades/${n.exam_id}/questoes/${n.question_number}`
    : `/aluno/treino/${n.exercicio_id}`
}

function linkDoContinuar(c) {
  if (c.origem === 'trilha') return `/aluno/treino/${c.exercicio_id}`
  if (c.situacao === 'proxima') return `/aluno/atividades/${c.exam_id}`
  return `/aluno/atividades/${c.exam_id}/questoes/${c.question_number}`
}

function Novidades({ itens }) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold text-gray-900">Novidades</h2>
      <div className="space-y-2">
        {itens.map(n => (
          <Link
            key={`${n.tipo}-${n.exam_id ?? ''}-${n.question_number ?? ''}-${n.exercicio_id ?? ''}`}
            to={linkDaNovidade(n)}
            className="flex items-center gap-3 bg-white rounded-xl border border-purple-200 p-4 hover:border-purple-400 transition-colors"
          >
            <span className="w-2 h-2 rounded-full bg-purple-600 shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-900">{TEXTO_DA_NOVIDADE[n.tipo]}</p>
              <p className="text-xs text-gray-500 truncate">{n.titulo}</p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}

function ProvaChegando({ prova }) {
  const navigate = useNavigate()
  const [gerando, setGerando] = useState(null)
  const [erro, setErro] = useState('')
  const feitos = prova.erros.filter(e => e.feito).length
  const tudoFeito = feitos === prova.erros.length

  const treinar = async (categoria) => {
    setErro('')
    setGerando(categoria)
    try {
      const { data } = await gerarExercicio(categoria)
      navigate(`/aluno/treino/${data.id}?via=prova_chegando`)
    } catch (e) {
      setErro(e.response?.data?.detail || 'Não foi possível abrir o treino agora.')
      setGerando(null)
    }
  }

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
      <div className="min-w-0">
        <h2 className="text-sm font-semibold text-gray-900 break-words">
          {prova.titulo} abre {prazoRelativo(prova.abre_em)}
        </h2>
        {prova.turma_nome && <p className="text-xs text-gray-400 truncate">{prova.turma_nome}</p>}
        <p className="text-sm text-gray-500 mt-1">
          Um treino curto com o que mais trava você. Nada aqui vale nota.
        </p>
      </div>

      <ul className="divide-y divide-gray-100">
        {prova.erros.map(e => (
          <li key={e.error_category} className="flex items-center justify-between gap-3 py-2">
            <span className="text-sm text-gray-700 min-w-0 break-words">{shortError(e.error_category)}</span>
            {e.feito ? (
              <span className="text-xs font-medium text-green-700 shrink-0">✓ feito</span>
            ) : (
              <button
                type="button"
                onClick={() => treinar(e.error_category)}
                disabled={gerando !== null}
                className="inline-flex items-center justify-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shrink-0"
              >
                {gerando === e.error_category && <Spinner className="w-4 h-4" />}
                Treinar
              </button>
            )}
          </li>
        ))}
      </ul>

      {gerando && (
        <p className="text-xs text-gray-500">Montando o exercício. Pode levar até meio minuto.</p>
      )}
      {erro && <p className="text-xs text-red-600">{erro}</p>}

      <p className="text-xs text-gray-400">
        {tudoFeito ? 'Treino feito' : `${feitos} de ${prova.erros.length} feitos`}
      </p>
    </section>
  )
}

function Continuar({ item }) {
  const emAndamento = item.situacao === 'em_andamento'
  const detalhes = [
    item.turma_nome,
    emAndamento && `${item.tentativas} tentativa${item.tentativas === 1 ? '' : 's'}`,
    emAndamento && item.ultimo_erro && `último erro: ${shortError(item.ultimo_erro)}`,
  ].filter(Boolean)

  return (
    <section className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col sm:flex-row sm:items-center gap-4">
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">
          {emAndamento ? 'Continuar de onde parou' : 'Próxima atividade'}
        </p>
        <p className="mt-1 text-sm font-medium text-gray-900 truncate">
          {item.origem === 'trilha' ? `Trilha · ${item.titulo}` : item.titulo}
        </p>
        {detalhes.length > 0 && (
          <p className="text-xs text-gray-400 mt-0.5">{detalhes.join(' · ')}</p>
        )}
      </div>
      <Link
        to={linkDoContinuar(item)}
        className="inline-flex items-center justify-center text-sm px-5 py-2.5 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 transition-colors"
      >
        {emAndamento ? 'Continuar' : 'Começar'}
      </Link>
    </section>
  )
}

function Prazos({ itens }) {
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold text-gray-900">Prazos próximos</h2>
      <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
        {itens.map(p => (
          <Link
            key={p.exam_id}
            to={`/aluno/atividades/${p.exam_id}`}
            className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-3 px-5 py-3 hover:bg-gray-50 transition-colors"
          >
            <div className="min-w-0">
              <p className="text-sm text-gray-900 truncate">{p.titulo}</p>
              <p className="text-xs text-gray-400 truncate">{p.turma_nome}</p>
            </div>
            <p className={`text-xs font-medium shrink-0 ${p.tipo === 'fecha' ? 'text-yellow-700' : 'text-purple-600'}`}>
              {modoLabel(p.modo)} · {p.tipo} {prazoRelativo(p.quando)}
            </p>
          </Link>
        ))}
      </div>
    </section>
  )
}

export default function InicioPage() {
  const [inicio, setInicio] = useState(null)
  const [erro, setErro] = useState(false)

  const carregar = () => getInicio()
    .then(({ data }) => { setInicio(data); setErro(false) })
    .catch(() => setErro(true))

  useEffect(() => { carregar() }, [])

  if (erro) {
    return (
      <div className="bg-white rounded-xl border border-dashed border-gray-200 p-10 text-center">
        <p className="text-sm text-gray-500">Não foi possível carregar o início.</p>
      </div>
    )
  }

  if (!inicio) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  // Conta nova cai aqui: uma tela só, com o que ela precisa fazer.
  if (!inicio.tem_turma) {
    return (
      <div className="max-w-md mx-auto py-10 space-y-4">
        <div className="text-center">
          <h1 className="text-xl font-semibold text-gray-900">Comece entrando na sua turma</h1>
          <p className="mt-1 text-sm text-gray-500">
            Suas atividades aparecem aqui assim que você entrar.
          </p>
        </div>
        <EntrarNaTurma aoEntrar={carregar} />
      </div>
    )
  }

  const { novidades, prova_chegando: provaChegando, continuar, prazos } = inicio
  const tudoEmDia = novidades.length === 0 && !provaChegando && !continuar && prazos.length === 0

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Início</h1>
        <p className="text-sm text-gray-400 mt-0.5">
          O que chegou para você, onde você parou e o que vence logo.
        </p>
      </div>

      {novidades.length > 0 && <Novidades itens={novidades} />}
      {provaChegando && <ProvaChegando prova={provaChegando} />}
      {continuar && <Continuar item={continuar} />}
      {prazos.length > 0 && <Prazos itens={prazos} />}

      {tudoEmDia && (
        <div className="bg-white rounded-xl border border-dashed border-gray-200 p-10 text-center">
          <p className="text-sm text-gray-500">Tudo em dia. Que tal treinar?</p>
          <Link
            to="/aluno/treino"
            className="mt-2 inline-block text-sm font-medium text-purple-600 hover:text-purple-700"
          >
            Ir para a trilha
          </Link>
        </div>
      )}
    </div>
  )
}
