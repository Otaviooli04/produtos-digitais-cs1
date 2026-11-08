import { GraduationCap, Presentation } from 'lucide-react'
import { Link } from 'react-router-dom'

// Alterna entre as duas portas de entrada do sistema, no login e no cadastro.
const DESTINOS = {
  login: { aluno: '/aluno/login', professor: '/login' },
  cadastro: { aluno: '/aluno/cadastro', professor: '/register' },
}

const PERFIS = [
  { chave: 'aluno', rotulo: 'Sou aluno', icone: GraduationCap },
  { chave: 'professor', rotulo: 'Sou professor', icone: Presentation },
]

export default function SeletorPerfil({ atual, contexto = 'login' }) {
  const destinos = DESTINOS[contexto]

  return (
    <div className="flex gap-1 mb-6">
      {PERFIS.map(({ chave, rotulo, icone }) => {
        const Icone = icone
        const ativo = chave === atual
        return (
          <Link
            key={chave}
            to={destinos[chave]}
            aria-current={ativo ? 'page' : undefined}
            className={`flex-1 flex items-center justify-center gap-1.5 min-h-11 text-sm font-semibold border-2 rounded-botao transition-colors ${
              ativo
                ? 'bg-lavanda text-violeta border-noite'
                : 'text-cinza-texto border-transparent hover:bg-lavanda hover:text-noite'
            }`}
          >
            <Icone className="w-4 h-4" />
            {rotulo}
          </Link>
        )
      })}
    </div>
  )
}
