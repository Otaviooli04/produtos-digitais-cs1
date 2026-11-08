import {
  ChartColumn, ClipboardList, FileCode, GraduationCap, LayoutDashboard, ListChecks, LogOut, Upload, User, Users,
} from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import Logo from './Logo'
import RotuloSecao from './ui/RotuloSecao'

const SECOES = ['panorama', 'atividades', 'desempenho']

function Item({ to, icone, ativo, children, aoNavegar }) {
  const Icone = icone
  return (
    <Link
      to={to}
      onClick={aoNavegar}
      aria-current={ativo ? 'page' : undefined}
      className={`flex items-center gap-2.5 min-h-11 px-3 rounded-botao text-sm font-semibold border-2 transition-colors ${
        ativo ? 'bg-lavanda border-noite text-violeta' : 'border-transparent text-noite hover:bg-lavanda'
      }`}
    >
      <Icone className="w-[18px] h-[18px] shrink-0" />
      <span className="truncate">{children}</span>
    </Link>
  )
}

function Grupo({ titulo, children }) {
  return (
    <div className="space-y-1">
      <RotuloSecao className="px-3 truncate" >{titulo}</RotuloSecao>
      {children}
    </div>
  )
}

export default function MenuLateral({ contexto, professor, aoSair, aoNavegar }) {
  const { pathname, search } = useLocation()
  const { turma, atividade } = contexto
  const pedida = new URLSearchParams(search).get('secao')
  const secao = SECOES.includes(pedida) ? pedida : 'panorama'

  const baseTurma = turma && `/turma/${turma.id}`
  const naPaginaDaTurma = pathname === baseTurma
  const baseAtividade = atividade && `/exam/${atividade.id}`
  const em = (sufixo) => Boolean(baseAtividade) && pathname.startsWith(`${baseAtividade}/${sufixo}`)

  return (
    <div className="h-full flex flex-col gap-6 p-5">
      <Link to="/" onClick={aoNavegar} aria-label="Início do CentralizEd"><Logo /></Link>

      <nav className="flex-1 space-y-6 overflow-y-auto">
        <div className="space-y-1">
          <Item to="/" icone={GraduationCap} ativo={pathname === '/'} aoNavegar={aoNavegar}>Turmas</Item>
        </div>

        {turma && (
          <Grupo titulo={turma.nome}>
            <Item to={`${baseTurma}?secao=panorama`} icone={LayoutDashboard} ativo={naPaginaDaTurma && secao === 'panorama'} aoNavegar={aoNavegar}>Panorama</Item>
            <Item
              to={`${baseTurma}?secao=atividades`}
              icone={ClipboardList}
              ativo={(naPaginaDaTurma && secao === 'atividades') || pathname === `${baseTurma}/upload`}
              aoNavegar={aoNavegar}
            >
              Atividades
            </Item>
            <Item to={`${baseTurma}?secao=desempenho`} icone={ChartColumn} ativo={naPaginaDaTurma && secao === 'desempenho'} aoNavegar={aoNavegar}>Desempenho</Item>
          </Grupo>
        )}

        {atividade && (
          <Grupo titulo={atividade.nome}>
            <Item to={baseAtividade} icone={ListChecks} ativo={pathname === baseAtividade || em('questions')} aoNavegar={aoNavegar}>Questões</Item>
            <Item to={`${baseAtividade}/students`} icone={Users} ativo={em('students')} aoNavegar={aoNavegar}>Alunos</Item>
            <Item to={`${baseAtividade}/results`} icone={ChartColumn} ativo={em('results')} aoNavegar={aoNavegar}>Resultados</Item>
            <Item to={`${baseAtividade}/submit`} icone={FileCode} ativo={em('submit')} aoNavegar={aoNavegar}>Testar submissão</Item>
            <Item to={`${baseAtividade}/bulk-submit`} icone={Upload} ativo={em('bulk-submit')} aoNavegar={aoNavegar}>Envio em lote</Item>
          </Grupo>
        )}
      </nav>

      <div className="space-y-1 pt-4 border-t-2 border-noite/10">
        <Item to="/profile" icone={User} ativo={pathname === '/profile'} aoNavegar={aoNavegar}>{professor.nome}</Item>
        <button
          type="button"
          onClick={aoSair}
          className="w-full flex items-center gap-2.5 min-h-11 px-3 rounded-botao text-sm font-semibold text-cinza-texto hover:bg-lavanda transition-colors"
        >
          <LogOut className="w-[18px] h-[18px] shrink-0" />
          Sair
        </button>
      </div>
    </div>
  )
}
