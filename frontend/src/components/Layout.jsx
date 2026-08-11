import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import JobDock from './JobDock'
import Logo from './Logo'

export default function Layout() {
  const { professor, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-3">
          <Link to="/" className="flex items-center gap-2.5 hover:opacity-80 transition-opacity">
            <Logo className="w-7 h-7" />
            <span className="font-semibold text-gray-900 text-sm">Analytics CS1</span>
          </Link>

          {professor && (
            <div className="flex items-center gap-3">
              <Link to="/profile" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
                <div className="w-7 h-7 rounded-full bg-purple-100 flex items-center justify-center">
                  <span className="text-xs font-semibold text-purple-600">
                    {professor.nome?.[0]?.toUpperCase()}
                  </span>
                </div>
                <span className="text-sm text-gray-700 hidden sm:block">{professor.nome}</span>
              </Link>
              <button
                onClick={handleLogout}
                className="text-xs px-3 py-1.5 rounded-lg border border-gray-200 text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </nav>
      <main className="max-w-6xl mx-auto px-6 py-8">
        <Outlet />
      </main>
      {professor && <JobDock />}
    </div>
  )
}
