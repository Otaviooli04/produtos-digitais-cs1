import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { AlunoAuthProvider } from './context/AlunoAuthContext'
import Layout from './components/Layout'
import AlunoLayout from './components/AlunoLayout'
import ProtectedRoute from './components/ProtectedRoute'
import AlunoProtectedRoute from './components/AlunoProtectedRoute'
import Spinner from './components/Spinner'

// Páginas em lazy-load para manter o bundle inicial leve.
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const UploadPage = lazy(() => import('./pages/UploadPage'))
const ExamDashboard = lazy(() => import('./pages/ExamDashboard'))
const TestCasesPage = lazy(() => import('./pages/TestCasesPage'))
const SubmitPage = lazy(() => import('./pages/SubmitPage'))
const ResultsPage = lazy(() => import('./pages/ResultsPage'))
const TurmaListPage = lazy(() => import('./pages/TurmaListPage'))
const TurmaDetailPage = lazy(() => import('./pages/TurmaDetailPage'))
const ExamUploadPage = lazy(() => import('./pages/ExamUploadPage'))
const SubmissionsPage = lazy(() => import('./pages/SubmissionsPage'))
const StudentSubmitPage = lazy(() => import('./pages/StudentSubmitPage'))
const BulkSubmitPage = lazy(() => import('./pages/BulkSubmitPage'))
const StudentsPage = lazy(() => import('./pages/StudentsPage'))
const StudentDetailPage = lazy(() => import('./pages/StudentDetailPage'))
const QuestionPage = lazy(() => import('./pages/QuestionPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const AlunoLoginPage = lazy(() => import('./pages/aluno/AlunoLoginPage'))
const AlunoRegisterPage = lazy(() => import('./pages/aluno/AlunoRegisterPage'))
const TurmasPage = lazy(() => import('./pages/aluno/TurmasPage'))
const TurmaPage = lazy(() => import('./pages/aluno/TurmaPage'))
const AtividadePage = lazy(() => import('./pages/aluno/AtividadePage'))
const QuestaoPage = lazy(() => import('./pages/aluno/QuestaoPage'))
const ProgressoPage = lazy(() => import('./pages/aluno/ProgressoPage'))
const AlunoPerfilPage = lazy(() => import('./pages/aluno/AlunoPerfilPage'))

function PageFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <Spinner className="w-6 h-6 text-purple-600" />
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AlunoAuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageFallback />}>
            <Routes>
              {/* Público — submissão avulsa, sem conta (link direto da prova) */}
              <Route path="submit/:examId" element={<StudentSubmitPage />} />

              {/* Aluno */}
              <Route path="aluno/login" element={<AlunoLoginPage />} />
              <Route path="aluno/cadastro" element={<AlunoRegisterPage />} />
              <Route element={<AlunoProtectedRoute />}>
                <Route element={<AlunoLayout />}>
                  <Route path="aluno" element={<Navigate to="/aluno/turmas" replace />} />
                  <Route path="aluno/turmas" element={<TurmasPage />} />
                  <Route path="aluno/turmas/:turmaId" element={<TurmaPage />} />
                  <Route path="aluno/progresso" element={<ProgressoPage />} />
                  <Route path="aluno/perfil" element={<AlunoPerfilPage />} />
                  <Route path="aluno/atividades/:examId" element={<AtividadePage />} />
                  <Route path="aluno/atividades/:examId/questoes/:numero" element={<QuestaoPage />} />
                </Route>
              </Route>

              {/* Auth */}
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />

              {/* Professor — protegido */}
              <Route element={<ProtectedRoute />}>
                <Route element={<Layout />}>
                  <Route index element={<TurmaListPage />} />
                  <Route path="profile" element={<ProfilePage />} />
                  <Route path="turma/:turmaId" element={<TurmaDetailPage />} />
                  <Route path="turma/:turmaId/upload" element={<ExamUploadPage />} />
                  <Route path="upload" element={<UploadPage />} />
                  <Route path="exam/:id" element={<ExamDashboard />} />
                  <Route path="exam/:id/questions/:num" element={<QuestionPage />} />
                  <Route path="exam/:id/questions/:num/testcases" element={<TestCasesPage />} />
                  <Route path="exam/:id/submit" element={<SubmitPage />} />
                  <Route path="exam/:id/results" element={<ResultsPage />} />
                  <Route path="exam/:id/questions/:num/submissions" element={<SubmissionsPage />} />
                  <Route path="exam/:id/bulk-submit" element={<BulkSubmitPage />} />
                  <Route path="exam/:id/students" element={<StudentsPage />} />
                  <Route path="exam/:id/students/:matricula" element={<StudentDetailPage />} />
                </Route>
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AlunoAuthProvider>
    </AuthProvider>
  )
}
