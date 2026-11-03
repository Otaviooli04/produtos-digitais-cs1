// O código do convite atravessa o cadastro ou o login guardado na aba. Sem
// sessionStorage (aba privada, bloqueio do navegador), o aluno só perde o atalho.
const CHAVE = 'convite_pendente'

export function guardarConvite(codigo) {
  try {
    sessionStorage.setItem(CHAVE, codigo)
  } catch {
    // sem armazenamento, segue sem o atalho
  }
}

export function lerConvite() {
  try {
    return sessionStorage.getItem(CHAVE)
  } catch {
    return null
  }
}

export function apagarConvite() {
  try {
    sessionStorage.removeItem(CHAVE)
  } catch {
    // sem armazenamento, não há o que apagar
  }
}
