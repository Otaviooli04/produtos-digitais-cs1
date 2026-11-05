import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { NOVIDADES_MUDARAM, contarNovidades, registrarAcesso } from '../api/aluno'
import { useAlunoAuth } from '../context/AlunoAuthContext'
import Logo from './Logo'

const linkClass = ({ isActive }) =>
  `text-sm px-3 py-1.5 rounded-lg transition-colors ${
    isActive ? 'bg-purple-50 text-purple-700 font-medium' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
  }`

function LinkInicio({ novidades }) {
  return (
    <NavLink to="/aluno" end className={linkClass}>
      <span className="inline-flex items-center gap-1.5">
        Início
        {novidades > 0 && (
          <span
            className="min-w-[1.125rem] h-[1.125rem] px-1 rounded-full bg-purple-600 text-white text-[10px] font-semibold leading-[1.125rem] text-center"
            aria-label={`${novidades} novidade${novidades === 1 ? '' : 's'}`}
          >
            {novidades > 9 ? '9+' : novidades}
          </span>
        )}
      </span>
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
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between gap-3">
          <div className="flex items-center gap-5">
            <Link to="/aluno" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
              <Logo className="w-7 h-7" />
              <span className="font-semibold text-gray-900 text-sm">Analytics CS1</span>
            </Link>
            <div className="hidden sm:flex items-center gap-1">
              <LinkInicio novidades={novidades} />
              <NavLink to="/aluno/turmas" className={linkClass}>Turmas</NavLink>
              <NavLink to="/aluno/treino" className={linkClass}>Treino</NavLink>
              <NavLink to="/aluno/progresso" className={linkClass}>Meu progresso</NavLink>
            </div>
          </div>

          {aluno && (
            <div className="flex items-center gap-3">
              <NavLink to="/aluno/perfil" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                <div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center">
                  <span className="text-xs font-semibold text-purple-600">
                    {aluno.nome?.[0]?.toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-gray-700 hidden sm:block">{aluno.nome}</span>
              </NavLink>
              <button
                onClick={handleLogout}
                className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Sair
              </button>
            </div>
          )}
        </div>
        <div className="sm:hidden border-t border-gray-100 px-6 py-2 flex gap-1">
          <LinkInicio novidades={novidades} />
          <NavLink to="/aluno/turmas" className={linkClass}>Turmas</NavLink>
          <NavLink to="/aluno/treino" className={linkClass}>Treino</NavLink>
          <NavLink to="/aluno/progresso" className={linkClass}>Meu progresso</NavLink>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}
