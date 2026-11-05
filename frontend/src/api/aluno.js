import alunoApi from './alunoClient'

export const NOVIDADES_MUDARAM = 'novidades:mudaram'

// Estas chamadas fazem o backend marcar uma novidade como vista. Avisar o menu
// na hora evita a bolinha só sumir na navegação seguinte.
const avisandoNovidades = (promessa) =>
  promessa.then((resposta) => {
    window.dispatchEvent(new Event(NOVIDADES_MUDARAM))
    return resposta
  })

export const registerAluno = (email, nome, matricula, senha) =>
  alunoApi.post('/aluno/register', { email, nome, matricula, senha })

export const loginAluno = (email, senha) =>
  alunoApi.post('/aluno/login', { email, senha })

export const getAlunoMe = () => alunoApi.get('/aluno/me')

export const updateAlunoMe = (nome, matricula) =>
  alunoApi.put('/aluno/me', { nome, matricula })

export const changeAlunoPassword = (senha_atual, senha_nova) =>
  alunoApi.put('/aluno/me/password', { senha_atual, senha_nova })

export const entrarNaTurma = (codigoAcesso, origem = 'codigo') =>
  alunoApi.post('/aluno/turmas/entrar', { codigo_acesso: codigoAcesso, origem })

export const listarMinhasTurmas = () => alunoApi.get('/aluno/turmas')

export const registrarAcesso = (via = null) =>
  alunoApi.post('/aluno/acessos', { via })

export const listarAtividades = (turmaId = null) =>
  alunoApi.get('/aluno/atividades', { params: turmaId ? { turma_id: turmaId } : {} })

export const getAtividade = (examId) => alunoApi.get(`/aluno/atividades/${examId}`)

export const submeterResposta = (examId, questionNumber, code) =>
  avisandoNovidades(alunoApi.post(`/aluno/atividades/${examId}/questoes/${questionNumber}/submissoes`, { code }))

export const getTentativas = (examId, questionNumber) =>
  avisandoNovidades(alunoApi.get(`/aluno/atividades/${examId}/questoes/${questionNumber}/tentativas`))

export const getProgresso = () => alunoApi.get('/aluno/progresso')

export const getErrosRecorrentes = () => alunoApi.get('/aluno/erros-recorrentes')

export const pedirAjuda = (submissionId, nivel) =>
  alunoApi.post(`/aluno/tentativas/${submissionId}/ajuda`, { nivel })

// ── trilha de treino ─────────────────────────────────────────────────────────

export const getTrilha = () => alunoApi.get('/aluno/treino')

export const gerarExercicio = (errorCategory = null) =>
  avisandoNovidades(alunoApi.post('/aluno/treino/gerar', { error_category: errorCategory }))

export const getExercicio = (exercicioId) =>
  avisandoNovidades(alunoApi.get(`/aluno/treino/${exercicioId}`))

export const treinar = (exercicioId, code) =>
  avisandoNovidades(alunoApi.post(`/aluno/treino/${exercicioId}/tentativas`, { code }))

export const reportarExercicio = (exercicioId, motivo) =>
  alunoApi.post(`/aluno/treino/${exercicioId}/reportar`, { motivo })

// ── início ───────────────────────────────────────────────────────────────────

export const getInicio = () => alunoApi.get('/aluno/inicio')

export const contarNovidades = () => alunoApi.get('/aluno/novidades/contagem')
