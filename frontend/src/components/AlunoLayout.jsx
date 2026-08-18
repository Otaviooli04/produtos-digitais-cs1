import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAlunoAuth } from '../context/AlunoAuthContext'
import Logo from './Logo'

const linkClass = ({ isActive }) =>
  `text-sm px-3 py-1.5 rounded-lg transition-colors ${
    isActive ? 'bg-purple-50 text-purple-700 font-medium' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
  }`

export default function AlunoLayout() {
  const { aluno, logout } = useAlunoAuth()
  const navigate = useNavigate()

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
              <NavLink to="/aluno" end className={linkClass}>Atividades</NavLink>
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
          <NavLink to="/aluno" end className={linkClass}>Atividades</NavLink>
          <NavLink to="/aluno/progresso" className={linkClass}>Meu progresso</NavLink>
        </div>
      </nav>
      <main className="max-w-5xl mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}
