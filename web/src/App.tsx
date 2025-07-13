import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import RoiReview from './pages/RoiReview'
import { AuthProvider, useAuth } from './context/AuthContext'
import type { ReactElement } from 'react'

function PrivateRoute({ children }: { children: ReactElement }) {
  const { loggedIn } = useAuth()
  return loggedIn ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={<PrivateRoute><Dashboard /></PrivateRoute>}
          />
          <Route
            path="/roi-review"
            element={<PrivateRoute><RoiReview /></PrivateRoute>}
          />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
