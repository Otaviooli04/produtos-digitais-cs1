import axios from 'axios'

// Cliente separado do painel do professor: o aluno tem token próprio e, ao
// expirar, volta para o login dele, não para o do professor.
const alunoApi = axios.create({
  baseURL: 'http://localhost:8000',
})

export const ALUNO_TOKEN_KEY = 'la_aluno_token'
export const ALUNO_KEY = 'la_aluno'

alunoApi.interceptors.request.use((config) => {
  const token = localStorage.getItem(ALUNO_TOKEN_KEY)
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

alunoApi.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem(ALUNO_TOKEN_KEY)
      localStorage.removeItem(ALUNO_KEY)
      window.location.href = '/aluno/login'
    }
    return Promise.reject(err)
  }
)

export default alunoApi
