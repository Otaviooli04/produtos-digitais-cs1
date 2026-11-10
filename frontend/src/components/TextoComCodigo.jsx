// O Gemini marca trechos de código com crases. Cada trecho vira <code> como
// elemento React, nunca HTML, então o texto do modelo continua sendo só texto.
export default function TextoComCodigo({ texto }) {
  const partes = String(texto ?? '').split('`')
  if (partes.length < 3 || partes.length % 2 === 0) return texto
  return (
    <>
      {partes.map((parte, i) => (
        i % 2 === 1
          ? <code key={i} className="font-mono text-[0.9em] text-noite bg-lavanda px-1 rounded-[5px] break-words">{parte}</code>
          : parte
      ))}
    </>
  )
}
