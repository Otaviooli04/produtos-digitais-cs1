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

// Redireciona para /login em 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('la_token')
      localStorage.removeItem('la_professor')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
