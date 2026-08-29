import api from './client'

export const uploadExam = (file, turmaId = null) => {
  const form = new FormData()
  form.append('file', file)
  if (turmaId) form.append('turma_id', String(turmaId))
  return api.post('/exam/upload', form)
}

export const getExam = (id) => api.get(`/exam/${id}`)

export const getJob = (jobId) => api.get(`/jobs/${jobId}`)

export const getActiveJobs = () => api.get('/jobs/active')

export const addTestCases = (examId, questionNumber, testCases) =>
  api.post(`/exam/${examId}/questions/${questionNumber}/testcases`, { test_cases: testCases })

export const getResults = (examId) => api.get(`/exam/${examId}/results`)

export const getGroups = (examId, questionNumber) =>
  api.get(`/exam/${examId}/questions/${questionNumber}/groups`)

export const runClustering = (examId, questionNumber, strategy) =>
  api.post(`/exam/${examId}/questions/${questionNumber}/cluster?strategy=${strategy}`)

export const runInsights = (examId, questionNumber, force = false) =>
  api.post(`/exam/${examId}/questions/${questionNumber}/insights${force ? '?force=true' : ''}`)

export const submitCode = (examId, questionNumber, code, matricula = '', dryRun = false) =>
  api.post('/submission/evaluate', {
    exam_id: Number(examId),
    question_number: questionNumber,
    code,
    matricula: matricula || null,
    dry_run: dryRun,
  })

export const bulkSubmit = (examId, file, format) => {
  const form = new FormData()
  form.append('file', file)
  form.append('format', format)
  return api.post(`/exam/${examId}/submissions/bulk`, form)
}

export const createTurma = (nome, codigo) =>
  api.post('/turmas', { nome, codigo })

export const updateTurma = (id, nome, codigo) =>
  api.put(`/turmas/${id}`, { nome, codigo })

export const deleteTurma = (id) => api.delete(`/turmas/${id}`)

export const deleteExam = (examId) => api.delete(`/exam/${examId}`)

export const updateExam = (examId, data) => api.patch(`/exam/${examId}`, data)

export const createQuestion = (examId, data) =>
  api.post(`/exam/${examId}/questions`, data)

export const updateQuestion = (examId, questionNumber, data) =>
  api.put(`/exam/${examId}/questions/${questionNumber}`, data)

export const deleteQuestion = (examId, questionNumber) =>
  api.delete(`/exam/${examId}/questions/${questionNumber}`)

export const deleteSubmission = (submissionId) =>
  api.delete(`/submission/${submissionId}`)

export const reevaluateSubmission = (submissionId) =>
  api.post(`/submission/${submissionId}/reevaluate`)

export const listTurmas = () => api.get('/turmas')

export const getTurma = (id) => api.get(`/turmas/${id}`)

export const getTurmaAnalytics = (id) => api.get(`/turmas/${id}/analytics`)

export const getQuestionSubmissions = (examId, questionNumber) =>
  api.get(`/exam/${examId}/questions/${questionNumber}/submissions`)

export const getExamStudents = (examId) => api.get(`/exam/${examId}/students`)

export const getStudentDetail = (examId, matricula) =>
  api.get(`/exam/${examId}/students/detail`, { params: { matricula } })

export const getTestCases = (examId, questionNumber) =>
  api.get(`/exam/${examId}/questions/${questionNumber}/testcases`)

export const deleteTestCase = (examId, questionNumber, tcId) =>
  api.delete(`/exam/${examId}/questions/${questionNumber}/testcases/${tcId}`)

export const updateTestCase = (examId, questionNumber, tcId, data) =>
  api.put(`/exam/${examId}/questions/${questionNumber}/testcases/${tcId}`, data)

export const getEffortReport = (examId) => api.get(`/exam/${examId}/effort-report`)
