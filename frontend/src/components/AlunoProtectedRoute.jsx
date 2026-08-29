import { Navigate, Outlet } from 'react-router-dom'
import { useAlunoAuth } from '../context/AlunoAuthContext'
import Spinner from './Spinner'

export default function AlunoProtectedRoute() {
  const { isAuthenticated, loading } = useAlunoAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner className="w-6 h-6 text-purple-600" />
      </div>
    )
  }

  return isAuthenticated ? <Outlet /> : <Navigate to="/aluno/login" replace />
}
