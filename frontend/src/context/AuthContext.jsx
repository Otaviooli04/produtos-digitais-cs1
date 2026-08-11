import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

const TOKEN_KEY = 'la_token'
const PROFESSOR_KEY = 'la_professor'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))
  const [professor, setProfessor] = useState(() => {
    try { return JSON.parse(localStorage.getItem(PROFESSOR_KEY)) } catch { return null }
  })
  // Já começa "carregando" quando há token salvo: o efeito abaixo valida-o.
  // Inicializar aqui evita um setState síncrono dentro do efeito.
  const [loading, setLoading] = useState(() => !!localStorage.getItem(TOKEN_KEY))

  const login = useCallback((accessToken, professorData) => {
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(PROFESSOR_KEY, JSON.stringify(professorData))
    setToken(accessToken)
    setProfessor(professorData)
  }, [])

  const updateProfessor = useCallback((professorData) => {
    localStorage.setItem(PROFESSOR_KEY, JSON.stringify(professorData))
    setProfessor(professorData)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(PROFESSOR_KEY)
    setToken(null)
    setProfessor(null)
  }, [])

  // Valida token ao iniciar; descarta se expirado.
  useEffect(() => {
    if (!token) return
    api.get('/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(({ data }) => setProfessor(data))
      .catch(() => logout())
      .finally(() => setLoading(false))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AuthContext.Provider value={{ professor, token, login, logout, updateProfessor, loading, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth deve ser usado dentro de AuthProvider')
  return ctx
}
