export default function Card({ principal = false, as = 'div', className = '', ...props }) {
  const Elemento = as
  return (
    <Elemento
      className={`bg-white border-2 border-noite rounded-card p-[22px] min-w-0 flex flex-col gap-3.5 ${principal ? 'shadow-bloco' : ''} ${className}`}
      {...props}
    />
  )
}
