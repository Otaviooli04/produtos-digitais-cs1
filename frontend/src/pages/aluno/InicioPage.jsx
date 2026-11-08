import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Check } from 'lucide-react'
import { gerarExercicio, getInicio } from '../../api/aluno'
import EntrarNaTurma from '../../components/EntrarNaTurma'
import Spinner from '../../components/Spinner'
import Botao from '../../components/ui/Botao'
import Card from '../../components/ui/Card'
import PainelDestaque from '../../components/ui/PainelDestaque'
import RotuloSecao from '../../components/ui/RotuloSecao'
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
    <section className="space-y-3">
      <RotuloSecao as="h2">Novidades</RotuloSecao>
      <div className="space-y-3">
        {itens.map(n => (
          <Link
            key={`${n.tipo}-${n.exam_id ?? ''}-${n.question_number ?? ''}-${n.exercicio_id ?? ''}`}
            to={linkDaNovidade(n)}
            className="flex items-center gap-3 bg-white border-2 border-noite rounded-card p-4 shadow-bloco transition-transform active:translate-x-0.5 active:translate-y-0.5"
          >
            <span className="w-2.5 h-2.5 rounded-full bg-coral shrink-0" aria-hidden="true" />
            <div className="min-w-0">
              <p className="font-bold">{TEXTO_DA_NOVIDADE[n.tipo]}</p>
              <p className="text-sm text-cinza-texto truncate">{n.titulo}</p>
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
    <Card as="section" principal>
      <div className="min-w-0">
        <h2 className="titulo-card break-words">
          {prova.titulo} abre {prazoRelativo(prova.abre_em)}
        </h2>
        {prova.turma_nome && <p className="text-xs text-cinza-texto truncate">{prova.turma_nome}</p>}
        <p className="text-sm text-cinza-texto mt-1">
          Um treino curto com o que mais trava você. Nada aqui vale nota.
        </p>
      </div>

      <ul className="divide-y divide-noite/10">
        {prova.erros.map(e => (
          <li key={e.error_category} className="flex items-center justify-between gap-3 py-2">
            <span className="text-sm text-cinza-texto min-w-0 break-words">{shortError(e.error_category)}</span>
            {e.feito ? (
              <span className="inline-flex items-center gap-1 text-[13px] font-bold text-sucesso shrink-0"><Check className="w-4 h-4" />feito</span>
            ) : (
              <Botao onClick={() => treinar(e.error_category)} disabled={gerando !== null} className="shrink-0">
                {gerando === e.error_category && <Spinner className="w-4 h-4" />}
                Treinar
              </Botao>
            )}
          </li>
        ))}
      </ul>

      {gerando && (
        <p className="text-xs text-cinza-texto">Montando o exercício. Pode levar até meio minuto.</p>
      )}
      {erro && <p className="text-xs text-erro">{erro}</p>}

      <p className="text-xs text-cinza-texto">
        {tudoFeito ? 'Treino feito' : `${feitos} de ${prova.erros.length} feitos`}
      </p>
    </Card>
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
    <PainelDestaque>
      <div className="flex flex-col sm:flex-row sm:items-center gap-5 pr-0 sm:pr-24">
        <div className="flex-1 min-w-0">
          <p className="font-titulo font-extrabold text-[13px] uppercase tracking-[0.1em] text-white/80">
            {emAndamento ? 'Continuar de onde parou' : 'Próxima atividade'}
          </p>
          <p className="mt-1 titulo-pagina break-words">
            {item.origem === 'trilha' ? `Trilha · ${item.titulo}` : item.titulo}
          </p>
          {detalhes.length > 0 && (
            <p className="text-sm text-white/80 mt-1">{detalhes.join(' · ')}</p>
          )}
        </div>
        <Botao to={linkDoContinuar(item)} variante="secundario" className="shrink-0">
          {emAndamento ? 'Bora continuar!' : 'Bora começar!'}
        </Botao>
      </div>
    </PainelDestaque>
  )
}

function Prazos({ itens }) {
  return (
    <section className="space-y-3">
      <RotuloSecao as="h2">Prazos próximos</RotuloSecao>
      <Card className="p-0! gap-0! divide-y-2 divide-noite/10 overflow-hidden">
        {itens.map(p => (
          <Link
            key={p.exam_id}
            to={`/aluno/atividades/${p.exam_id}`}
            className="flex flex-col gap-1 px-5 py-3 hover:bg-lavanda transition-colors"
          >
            <p className="font-bold truncate">{p.titulo}</p>
            <p className="text-sm text-cinza-texto truncate">{p.turma_nome}</p>
            <p className={`text-[13px] font-bold ${p.tipo === 'fecha' ? 'text-aviso' : 'text-violeta'}`}>
              {modoLabel(p.modo)} · {p.tipo} {prazoRelativo(p.quando)}
            </p>
          </Link>
        ))}
      </Card>
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
      <Card className="border-dashed border-noite/30! text-center p-10!">
        <p className="text-cinza-texto">Não foi possível carregar o início.</p>
      </Card>
    )
  }

  if (!inicio) {
    return (
      <div className="flex items-center justify-center py-20">
        <Spinner className="w-6 h-6 text-violeta" />
      </div>
    )
  }

  // Conta nova cai aqui: uma tela só, com o que ela precisa fazer.
  if (!inicio.tem_turma) {
    return (
      <div className="max-w-md mx-auto py-10 space-y-4">
        <div className="text-center">
          <h1 className="titulo-pagina">Comece entrando na sua turma</h1>
          <p className="mt-1 text-sm text-cinza-texto">
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
      {continuar ? (
        <Continuar item={continuar} />
      ) : (
        <div>
          <h1 className="titulo-pagina">Início</h1>
          <p className="text-cinza-texto mt-1">O que chegou para você, onde você parou e o que vence logo.</p>
        </div>
      )}

      {(novidades.length > 0 || provaChegando || prazos.length > 0) && (
        <div className="grid gap-8 lg:grid-cols-2 items-start">
          {(novidades.length > 0 || provaChegando) && (
            <div className="space-y-8 min-w-0">
              {novidades.length > 0 && <Novidades itens={novidades} />}
              {provaChegando && <ProvaChegando prova={provaChegando} />}
            </div>
          )}
          {prazos.length > 0 && <div className="min-w-0"><Prazos itens={prazos} /></div>}
        </div>
      )}

      {tudoEmDia && (
        <Card className="border-dashed border-noite/30! text-center p-10!">
          <p className="text-cinza-texto">Tudo em dia. Que tal treinar?</p>
          <Botao to="/aluno/treino" className="self-center">Bora treinar!</Botao>
        </Card>
      )}
    </div>
  )
}
