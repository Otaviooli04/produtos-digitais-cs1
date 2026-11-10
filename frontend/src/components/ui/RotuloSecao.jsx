export default function RotuloSecao({ as = 'p', className = '', title, children }) {
  const Elemento = as
  return (
    <Elemento className={`font-titulo font-extrabold text-[13px] uppercase tracking-[0.1em] text-cinza-texto ${className}`} title={title}>
      {children}
    </Elemento>
  )
}
