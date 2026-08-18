import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import alunoApi, { ALUNO_KEY, ALUNO_TOKEN_KEY } from '../api/alunoClient'

const AlunoAuthContext = createContext(null)

export function AlunoAuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(ALUNO_TOKEN_KEY))
  const [aluno, setAluno] = useState(() => {
    try { return JSON.parse(localStorage.getItem(ALUNO_KEY)) } catch { return null }
  })
  const [loading, setLoading] = useState(() => !!localStorage.getItem(ALUNO_TOKEN_KEY))

  const login = useCallback((accessToken, alunoData) => {
    localStorage.setItem(ALUNO_TOKEN_KEY, accessToken)
    localStorage.setItem(ALUNO_KEY, JSON.stringify(alunoData))
    setToken(accessToken)
    setAluno(alunoData)
  }, [])

  const updateAluno = useCallback((alunoData) => {
    localStorage.setItem(ALUNO_KEY, JSON.stringify(alunoData))
    setAluno(alunoData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(ALUNO_TOKEN_KEY)
    localStorage.removeItem(ALUNO_KEY)
    setToken(null)
    setAluno(null)
  }, [])

  // Valida o token guardado ao abrir o app; descarta se expirou.
  useEffect(() => {
    if (!token) return
    alunoApi.get('/aluno/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(({ data }) => setAluno(data))
      .catch(() => logout())
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AlunoAuthContext.Provider
      value={{ aluno, token, login, logout, updateAluno, loading, isAuthenticated: !!token }}
    >
      {children}
    </AlunoAuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAlunoAuth() {
  const ctx = useContext(AlunoAuthContext)
  if (!ctx) throw new Error('useAlunoAuth deve ser usado dentro de AlunoAuthProvider')
  return ctx
}
