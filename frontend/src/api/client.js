import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

// Injeta token em todas as requisições
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('la_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Redireciona para /login em 401. O 401 do próprio login é e-mail ou senha
// errados: fica na tela, sem recarregar a página e apagar o que foi digitado.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && err.config?.url !== '/auth/login') {
      localStorage.removeItem('la_token')
      localStorage.removeItem('la_professor')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
