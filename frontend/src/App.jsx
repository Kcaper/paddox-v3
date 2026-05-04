import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'

function ComingSoon({ page }) {
  return (
    <div className="flex items-center justify-center min-h-screen text-white">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-red-500 mb-2">Paddox</h1>
        <p className="text-gray-400">{page} — coming soon</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ComingSoon page="Dashboard" />} />
        <Route path="/racely" element={<ComingSoon page="Racely Predictions" />} />
        <Route path="/driver-predictions/:paddockId" element={<ComingSoon page="Driver Predictions" />} />
        <Route path="/team-predictions/:paddockId" element={<ComingSoon page="Team Predictions" />} />
        <Route path="/quiz" element={<ComingSoon page="Race Quiz" />} />
        <Route path="/create-paddock" element={<ComingSoon page="Create Paddock" />} />
        <Route path="/join-paddock" element={<ComingSoon page="Join Paddock" />} />
        <Route path="/my-paddocks" element={<ComingSoon page="My Paddocks" />} />
        <Route path="/paddock/:id" element={<ComingSoon page="Paddock" />} />
        <Route path="/leaderboard/:paddockId/:type" element={<ComingSoon page="Leaderboard" />} />
        <Route path="/profile" element={<ComingSoon page="Profile" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
