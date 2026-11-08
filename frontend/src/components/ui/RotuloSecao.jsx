export default function RotuloSecao({ as = 'p', className = '', children }) {
  const Elemento = as
  return (
    <Elemento className={`font-titulo font-extrabold text-[13px] uppercase tracking-[0.1em] text-cinza-texto ${className}`}>
      {children}
    </Elemento>
  )
}
