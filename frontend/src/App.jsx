import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Racely from './pages/Racely'
import MyPaddocks from './pages/MyPaddocks'
import PaddockDetail from './pages/PaddockDetail'
import SeasonPredictions from './pages/SeasonPredictions'
import Quiz from './pages/Quiz'
import Profile from './pages/Profile'

function ComingSoon({ page }) {
  return (
    <div className="flex items-center justify-center min-h-[60vh] text-white">
      <div className="text-center">
        <p className="text-gray-500 text-sm">{page} — coming soon</p>
      </div>
    </div>
  )
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      {/* Public auth routes — redirect to home if already logged in */}
      <Route
        path="/login"
        element={user && user !== undefined ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/register"
        element={user && user !== undefined ? <Navigate to="/" replace /> : <Register />}
      />

      {/* Protected app routes */}
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/racely" element={<Racely />} />
                <Route path="/driver-predictions/:paddockId" element={<SeasonPredictions />} />
                <Route path="/team-predictions/:paddockId" element={<SeasonPredictions />} />
                <Route path="/quiz" element={<Quiz />} />
                <Route path="/create-paddock" element={<ComingSoon page="Create Paddock" />} />
                <Route path="/join-paddock" element={<ComingSoon page="Join Paddock" />} />
                <Route path="/my-paddocks" element={<MyPaddocks />} />
                <Route path="/paddock/:id" element={<PaddockDetail />} />
                <Route path="/leaderboard/:paddockId/:type" element={<ComingSoon page="Leaderboard" />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
