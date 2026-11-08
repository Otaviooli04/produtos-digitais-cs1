import { useEffect, useRef, useState } from 'react'
import { GraduationCap, House, LogOut, Target, TrendingUp } from 'lucide-react'
import { Link, NavLink, Outlet, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { NOVIDADES_MUDARAM, contarNovidades, registrarAcesso } from '../api/aluno'
import { useAlunoAuth } from '../context/AlunoAuthContext'
import Logo from './Logo'

const linkClass = ({ isActive }) =>
  `min-h-11 inline-flex items-center px-3 rounded-botao text-sm font-semibold transition-colors whitespace-nowrap ${
    isActive ? 'bg-lavanda text-violeta' : 'text-noite hover:bg-lavanda'
  }`

function Bolinha({ novidades }) {
  if (novidades <= 0) return null
  return (
    <span className="inline-block min-w-[1.125rem] h-[1.125rem] px-1 rounded-full bg-coral text-noite text-[10px] font-bold leading-[1.125rem] text-center">
      <span aria-hidden="true">{novidades > 9 ? '9+' : novidades}</span>
      <span className="sr-only">{`${novidades} novidade${novidades === 1 ? '' : 's'}`}</span>
    </span>
  )
}

function Aba({ to, end, icone, rotulo, novidades = 0 }) {
  const Icone = icone
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `relative flex flex-col items-center justify-center gap-0.5 min-h-14 text-[11px] font-bold ${
          isActive ? 'text-violeta' : 'text-cinza-texto'
        }`
      }
    >
      <span className="relative">
        <Icone className="w-[22px] h-[22px]" />
        <span className="absolute -top-1.5 left-4"><Bolinha novidades={novidades} /></span>
      </span>
      {rotulo}
    </NavLink>
  )
}

export default function AlunoLayout() {
  const { aluno, logout } = useAlunoAuth()
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const via = searchParams.get('via')
  const registrou = useRef(false)
  const { pathname } = useLocation()
  const [novidades, setNovidades] = useState(0)
  const sequencia = useRef(0)

  // RF20: a bolinha do Início, refeita a cada troca de página e quando uma
  // chamada avisa que marcou algo como visto (o evento NOVIDADES_MUDARAM).
  useEffect(() => {
    let ativo = true
    const atualizar = () => {
      const meuNumero = ++sequencia.current
      const maisRecente = () => ativo && meuNumero === sequencia.current
      contarNovidades()
        .then(({ data }) => { if (maisRecente()) setNovidades(data.total) })
        .catch(() => { if (maisRecente()) setNovidades(0) })
    }
    atualizar()
    window.addEventListener(NOVIDADES_MUDARAM, atualizar)
    return () => {
      ativo = false
      window.removeEventListener(NOVIDADES_MUDARAM, atualizar)
    }
  }, [pathname])

  // RF14: cada abertura do app vira um acesso. O servidor descarta o que vier
  // perto demais de outro, então aqui não há controle de tempo. Tirar o `via`
  // da URL não conta como abertura nova.
  useEffect(() => {
    if (registrou.current && !via) return
    registrou.current = true
    registrarAcesso(via).catch(() => {})
    if (via) setSearchParams(params => { params.delete('via'); return params }, { replace: true })
  }, [via, setSearchParams])

  useEffect(() => {
    const aoVoltar = () => {
      if (document.visibilityState === 'visible') registrarAcesso().catch(() => {})
    }
    document.addEventListener('visibilitychange', aoVoltar)
    return () => document.removeEventListener('visibilitychange', aoVoltar)
  }, [])

  const handleLogout = () => {
    logout()
    navigate('/aluno/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-white">
      <nav className="bg-white border-b-2 border-noite sm:sticky sm:top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-3">
          <div className="flex items-center gap-6">
            <Link to="/aluno" aria-label="Início do CentralizEd"><Logo /></Link>
            <div className="hidden sm:flex items-center gap-1">
              <NavLink to="/aluno" end className={linkClass}>
                <span className="inline-flex items-center gap-1.5">Início <Bolinha novidades={novidades} /></span>
              </NavLink>
              <NavLink to="/aluno/turmas" className={linkClass}>Turmas</NavLink>
              <NavLink to="/aluno/treino" className={linkClass}>Treino</NavLink>
              <NavLink to="/aluno/progresso" className={linkClass}>Meu progresso</NavLink>
            </div>
          </div>

          {aluno && (
            <div className="flex items-center gap-1">
              <NavLink to="/aluno/perfil" className="min-h-11 flex items-center gap-2 px-2 rounded-botao hover:bg-lavanda transition-colors">
                <span className="w-8 h-8 rounded-full bg-lavanda border-2 border-noite flex items-center justify-center text-xs font-bold text-violeta">
                  {aluno.nome?.[0]?.toUpperCase()}
                </span>
                <span className="text-sm font-semibold hidden sm:block">{aluno.nome}</span>
              </NavLink>
              <button
                type="button"
                onClick={handleLogout}
                aria-label="Sair"
                className="min-h-11 min-w-11 inline-flex items-center justify-center rounded-botao text-cinza-texto hover:bg-lavanda transition-colors"
              >
                <LogOut className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-5 sm:py-8 pb-[calc(6rem+env(safe-area-inset-bottom))] sm:pb-8">
        <Outlet />
      </main>

      <nav
        aria-label="Navegação principal"
        className="sm:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t-2 border-noite grid grid-cols-4 pb-[env(safe-area-inset-bottom)]"
      >
        <Aba to="/aluno" end icone={House} rotulo="Início" novidades={novidades} />
        <Aba to="/aluno/turmas" icone={GraduationCap} rotulo="Turmas" />
        <Aba to="/aluno/treino" icone={Target} rotulo="Treino" />
        <Aba to="/aluno/progresso" icone={TrendingUp} rotulo="Progresso" />
      </nav>
    </div>
  )
}
