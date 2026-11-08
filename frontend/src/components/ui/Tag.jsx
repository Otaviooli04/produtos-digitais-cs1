const VARIANTES = {
  violeta: 'bg-lavanda text-violeta',
  sucesso: 'bg-sucesso-fundo text-sucesso',
  erro: 'bg-erro-fundo text-erro',
  aviso: 'bg-aviso-fundo text-aviso',
  neutro: 'bg-lavanda text-cinza-texto',
}

export default function Tag({ variante = 'violeta', children }) {
  return (
    <span className={`inline-flex items-center text-[13px] font-bold px-3 py-[5px] rounded-tag ${VARIANTES[variante]}`}>
      {children}
    </span>
  )
}
