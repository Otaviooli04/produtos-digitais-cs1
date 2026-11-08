import { Link } from 'react-router-dom'

const VARIANTES = {
  primario: 'bg-violeta text-white hover:bg-violeta-escuro',
  secundario: 'bg-white text-noite hover:bg-lavanda',
  perigo: 'bg-white text-erro hover:bg-erro-fundo',
}

export default function Botao({ variante = 'primario', to, className = '', ...props }) {
  const classes = `inline-flex items-center justify-center gap-2 min-h-11 px-[22px] border-2 border-noite rounded-botao font-bold text-[15px] transition-transform active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed ${VARIANTES[variante]} ${className}`
  if (to) return <Link to={to} className={classes} {...props} />
  return <button type="button" className={classes} {...props} />
}
