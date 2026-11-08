/**
 * O que o envio recém-feito diz em relação aos anteriores: quanto avançou e,
 * quando os envios viraram tentativa às cegas, uma sugestão de pausa. A pausa
 * vem antes de qualquer comemoração, por isso aparece primeiro.
 */
export default function RitmoDaTentativa({ avanco, sugerirPausa, semCasos = false }) {
  const mais = avanco?.casos_a_mais ?? 0

  return (
    <>
      {sugerirPausa && (
        <div className="rounded-xl border border-aviso/30 bg-aviso-fundo px-4 py-3">
          <p className="text-sm font-medium text-aviso">Que tal uma pausa de um minuto?</p>
          <p className="text-xs text-aviso mt-1">
            Foram três envios em poucos minutos, com o código quase igual e o mesmo resultado.
            {semCasos
              ? ' Antes do próximo, leia com calma a mensagem do compilador abaixo e procure a linha que ela aponta.'
              : ' Antes do próximo, releia o caso que falhou abaixo e tente dizer, com suas palavras, o que o seu programa faz com aquela entrada.'}
          </p>
        </div>
      )}

      {avanco && mais > 0 && (
        <div className="rounded-xl border border-sucesso/30 bg-sucesso-fundo px-4 py-2.5 text-sm text-sucesso">
          Passou em {mais} caso{mais > 1 ? 's' : ''} a mais que na tentativa anterior
          ({avanco.passados_antes} → {avanco.passados} de {avanco.total}).
        </div>
      )}

      {avanco && mais < 0 && (
        <div className="rounded-xl border border-noite/20 bg-white px-4 py-2.5 text-sm text-cinza-texto">
          Passou em {-mais} caso{mais < -1 ? 's' : ''} a menos que na tentativa anterior
          ({avanco.passados_antes} → {avanco.passados} de {avanco.total}).
          Compare o que mudou entre as duas.
        </div>
      )}
    </>
  )
}
