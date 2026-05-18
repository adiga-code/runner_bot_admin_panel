import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ToastProvider } from './components/Toast'
import Login from './pages/Login'
import Layout from './components/Layout'
import Users from './pages/Users'
import UserDetail from './pages/UserDetail'
import Workouts from './pages/Workouts'
import WorkoutTemplates from './pages/WorkoutTemplates'
import Analytics from './pages/Analytics'
import Approvals from './pages/Approvals'
import PendingUsers from './pages/PendingUsers'
import Materials from './pages/Materials'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token')
  if (!token) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter basename={import.meta.env.BASE_URL.replace(/\/$/, '') || '/'}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/pending" replace />} />
            <Route path="pending" element={<PendingUsers />} />
            <Route path="approvals" element={<Approvals />} />
            <Route path="users" element={<Users />} />
            <Route path="users/:id" element={<UserDetail />} />
            <Route path="materials" element={<Materials />} />
            <Route path="workouts" element={<Workouts />} />
            <Route path="workout-templates" element={<WorkoutTemplates />} />
            <Route path="analytics" element={<Analytics />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ToastProvider>
  )
}
