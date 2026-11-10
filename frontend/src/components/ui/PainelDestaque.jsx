import { SimboloOrbita } from '../Logo'

export default function PainelDestaque({ className = '', children }) {
  return (
    <section className={`[&_:focus-visible]:outline-white relative overflow-hidden bg-violeta text-white border-2 border-noite rounded-card p-6 sm:p-8 ${className}`}>
      <SimboloOrbita fundo="violeta" className="absolute -right-20 -top-20 w-80 h-80 opacity-25 pointer-events-none" />
      <div className="relative">{children}</div>
    </section>
  )
}
