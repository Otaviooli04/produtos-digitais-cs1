import api from './client'

export const register = (email, nome, senha) =>
  api.post('/auth/register', { email, nome, senha })

export const login = (email, senha) =>
  api.post('/auth/login', { email, senha })

export const getMe = () =>
  api.get('/auth/me')

export const updateProfile = (nome) =>
  api.put('/auth/me', { nome })

export const changePassword = (senha_atual, senha_nova) =>
  api.put('/auth/me/password', { senha_atual, senha_nova })
