const CORES = {
  claro: { traco: '#4A2EE0', nome: 'text-noite', ed: 'text-violeta' },
  violeta: { traco: '#FFFFFF', nome: 'text-white', ed: 'text-coral' },
}

export function SimboloOrbita({ fundo = 'claro', className = '' }) {
  const { traco } = CORES[fundo]
  return (
    <svg className={className} viewBox="0 0 84 84" aria-hidden="true">
      <circle cx="42" cy="42" r="38" fill="none" stroke={traco} strokeWidth="3" />
      <circle cx="42" cy="42" r="23" fill="none" stroke={traco} strokeWidth="3" opacity="0.45" />
      <circle cx="42" cy="42" r="10" fill={traco} />
      <circle cx="69" cy="15" r="7" fill="#FF6B4A" />
      <circle cx="20" cy="56" r="5" fill={traco} />
    </svg>
  )
}

const TAMANHOS = {
  md: { simbolo: 'w-8 h-8', texto: 'text-[22px]', espaco: 'gap-2.5' },
  lg: { simbolo: 'w-12 h-12', texto: 'text-[32px]', espaco: 'gap-[18px]' },
}

// Sobre violeta use sempre tamanho `lg`: o guia só aceita coral sobre violeta a partir de 32 px.
export default function Logo({ fundo = 'claro', tamanho = 'md', soSimbolo = false }) {
  const t = TAMANHOS[tamanho]
  const { nome, ed } = CORES[fundo]
  if (soSimbolo) return <SimboloOrbita fundo={fundo} className={t.simbolo} />
  return (
    <span className={`inline-flex items-center ${t.espaco}`}>
      <SimboloOrbita fundo={fundo} className={t.simbolo} />
      <span className={`font-logo font-medium tracking-[-0.03em] ${t.texto} ${nome}`}>
        centraliz<span className={`font-bold ${ed}`}>Ed</span>
      </span>
    </span>
  )
}
