import alunoApi from './alunoClient'

export const registerAluno = (email, nome, matricula, senha) =>
  alunoApi.post('/aluno/register', { email, nome, matricula, senha })

export const loginAluno = (email, senha) =>
  alunoApi.post('/aluno/login', { email, senha })

export const getAlunoMe = () => alunoApi.get('/aluno/me')

export const updateAlunoMe = (nome, matricula) =>
  alunoApi.put('/aluno/me', { nome, matricula })

export const changeAlunoPassword = (senha_atual, senha_nova) =>
  alunoApi.put('/aluno/me/password', { senha_atual, senha_nova })

export const entrarNaTurma = (codigoAcesso) =>
  alunoApi.post('/aluno/turmas/entrar', { codigo_acesso: codigoAcesso })

export const listarMinhasTurmas = () => alunoApi.get('/aluno/turmas')

export const listarAtividades = (turmaId = null) =>
  alunoApi.get('/aluno/atividades', { params: turmaId ? { turma_id: turmaId } : {} })

export const getAtividade = (examId) => alunoApi.get(`/aluno/atividades/${examId}`)

export const submeterResposta = (examId, questionNumber, code) =>
  alunoApi.post(`/aluno/atividades/${examId}/questoes/${questionNumber}/submissoes`, { code })

export const getTentativas = (examId, questionNumber) =>
  alunoApi.get(`/aluno/atividades/${examId}/questoes/${questionNumber}/tentativas`)

export const getProgresso = () => alunoApi.get('/aluno/progresso')

export const getErrosRecorrentes = () => alunoApi.get('/aluno/erros-recorrentes')
