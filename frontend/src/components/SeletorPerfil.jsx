import { Link } from 'react-router-dom'

// Alterna entre as duas portas de entrada do sistema, no login e no cadastro.
const DESTINOS = {
  login: { aluno: '/aluno/login', professor: '/login' },
  cadastro: { aluno: '/aluno/cadastro', professor: '/register' },
}

const PERFIS = [
  { chave: 'aluno', rotulo: 'Sou aluno' },
  { chave: 'professor', rotulo: 'Sou professor' },
]

function IconeAluno({ className }) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 3.5 2.5 7.2 10 11l7.5-3.8L10 3.5Z" />
      <path d="M5.5 9v3.8c0 1.2 2 2.2 4.5 2.2s4.5-1 4.5-2.2V9" />
      <path d="M17.5 7.2v4.3" />
    </svg>
  )
}

function IconeProfessor({ className }) {
  return (
    <svg className={className} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2.5" y="3.5" width="15" height="10" rx="1.5" />
      <path d="M6 16.5h8" />
      <path d="M5.8 10.6 8.4 8l2 2 3.8-3.8" />
    </svg>
  )
}

export default function SeletorPerfil({ atual, contexto = 'login' }) {
  const destinos = DESTINOS[contexto]

  return (
    <div className="flex gap-1 p-1 mb-6 bg-gray-100 rounded-xl">
      {PERFIS.map(({ chave, rotulo }) => {
        const ativo = chave === atual
        const cor = ativo ? 'text-purple-600' : 'text-gray-400'
        return (
          <Link
            key={chave}
            to={destinos[chave]}
            aria-current={ativo ? 'page' : undefined}
            className={`flex-1 flex items-center justify-center gap-1.5 text-sm py-2 rounded-lg transition-all ${
              ativo
                ? 'bg-white text-purple-700 font-medium shadow-sm ring-1 ring-black/5'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {chave === 'aluno'
              ? <IconeAluno className={`w-4 h-4 ${cor}`} />
              : <IconeProfessor className={`w-4 h-4 ${cor}`} />}
            {rotulo}
          </Link>
        )
      })}
    </div>
  )
}
