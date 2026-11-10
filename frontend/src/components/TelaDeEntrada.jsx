import Logo, { SimboloOrbita } from './Logo'

export default function TelaDeEntrada({ frase, children }) {
  return (
    <div className="min-h-screen bg-white lg:grid lg:grid-cols-2">
      <div className="relative overflow-hidden bg-violeta text-white border-b-2 lg:border-b-0 lg:border-r-2 border-noite px-6 py-6 lg:p-14 flex flex-col lg:justify-between">
        <SimboloOrbita fundo="violeta" className="absolute -right-24 -bottom-24 w-[28rem] h-[28rem] opacity-25 pointer-events-none" />
        <div className="relative"><Logo fundo="violeta" tamanho="lg" /></div>
        <p className="relative hidden lg:block titulo-pagina max-w-md">{frase}</p>
      </div>
      <div className="flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-sm">{children}</div>
      </div>
    </div>
  )
}
