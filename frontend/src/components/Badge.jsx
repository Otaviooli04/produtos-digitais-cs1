const variants = {
  green:  'bg-sucesso-fundo text-sucesso ring-sucesso/20',
  red:    'bg-erro-fundo text-erro ring-erro/20',
  yellow: 'bg-aviso-fundo text-aviso ring-aviso/20',
  purple: 'bg-lavanda text-violeta ring-violeta/20',
  gray:   'bg-lavanda text-cinza-texto ring-noite/20',
}

export default function Badge({ color = 'gray', children }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${variants[color]}`}>
      {children}
    </span>
  )
}
