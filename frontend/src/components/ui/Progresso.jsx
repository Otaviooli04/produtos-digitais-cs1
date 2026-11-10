export default function Progresso({ valor, rotulo, cor }) {
  const limitado = Math.max(0, Math.min(100, valor))
  return (
    <div
      role="progressbar"
      aria-label={rotulo}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(limitado)}
      className="h-2.5 rounded-[5px] bg-lavanda overflow-hidden"
    >
      <div className={`h-2.5 rounded-[5px] ${cor ? '' : 'bg-coral'}`} style={{ width: `${limitado}%`, ...(cor ? { backgroundColor: cor } : {}) }} />
    </div>
  )
}
