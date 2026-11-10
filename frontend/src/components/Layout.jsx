import { useEffect, useState } from 'react'
import { Menu, X } from 'lucide-react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import useContextoProfessor from '../hooks/useContextoProfessor'
import JobDock from './JobDock'
import Logo from './Logo'
import MenuLateral from './MenuLateral'

export default function Layout() {
  const { professor, logout } = useAuth()
  const navigate = useNavigate()
  const contexto = useContextoProfessor()
  const { pathname, search } = useLocation()
  const aqui = pathname + search
  // Guarda onde a gaveta foi aberta: navegar para outro lugar já a fecha.
  const [gavetaEm, setGavetaEm] = useState(null)
  const gavetaAberta = gavetaEm === aqui

  useEffect(() => {
    if (!gavetaAberta) return undefined
    const aoTeclar = (e) => { if (e.key === 'Escape') setGavetaEm(null) }
    window.addEventListener('keydown', aoTeclar)
    return () => window.removeEventListener('keydown', aoTeclar)
  }, [gavetaAberta])

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const menu = professor && (
    <MenuLateral
      contexto={contexto}
      professor={professor}
      aoSair={handleLogout}
      aoNavegar={() => setGavetaEm(null)}
    />
  )

  return (
    <div className="min-h-screen bg-white lg:grid lg:grid-cols-[272px_minmax(0,1fr)]">
      <aside className="hidden lg:block sticky top-0 h-screen border-r-2 border-noite">
        {menu}
      </aside>

      <header className="lg:hidden sticky top-0 z-30 bg-white border-b-2 border-noite h-14 px-4 flex items-center justify-between">
        <Link to="/" aria-label="Início do CentralizEd"><Logo /></Link>
        {professor && (
          <button
            type="button"
            onClick={() => setGavetaEm(aqui)}
            aria-label="Abrir menu"
            aria-expanded={gavetaAberta}
            className="min-h-11 min-w-11 inline-flex items-center justify-center rounded-botao hover:bg-lavanda"
          >
            <Menu className="w-6 h-6" />
          </button>
        )}
      </header>

      {gavetaAberta && (
        <div className="lg:hidden fixed inset-0 z-50">
          <button
            type="button"
            aria-label="Fechar menu"
            onClick={() => setGavetaEm(null)}
            className="absolute inset-0 w-full h-full bg-noite/40"
          />
          <aside
            role="dialog"
            aria-modal="true"
            aria-label="Menu"
            className="absolute inset-y-0 left-0 w-[280px] max-w-[85vw] bg-white border-r-2 border-noite"
          >
            <button
              type="button"
              autoFocus
              onClick={() => setGavetaEm(null)}
              aria-label="Fechar menu"
              className="absolute top-3 right-3 z-10 min-h-11 min-w-11 inline-flex items-center justify-center rounded-botao hover:bg-lavanda"
            >
              <X className="w-5 h-5" />
            </button>
            {menu}
          </aside>
        </div>
      )}

      <main className="min-w-0 w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-10 py-6 lg:py-10">
        <Outlet context={{ contexto }} />
      </main>
      {professor && <JobDock />}
    </div>
  )
}
