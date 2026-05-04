import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { paddocksApi } from '../api/paddocks'

export default function PaddockDetail() {
  const { id } = useParams()
  const [paddock, setPaddock] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [tab, setTab] = useState('leaderboard')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      paddocksApi.detail(id),
      paddocksApi.leaderboard(id),
    ]).then(([pd, lb]) => {
      setPaddock(pd.data)
      setLeaderboard(lb.data.leaderboard || [])
    }).finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!paddock) return <div className="p-8 text-gray-500">Paddock not found.</div>

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1">
          <Link to="/my-paddocks" className="text-gray-500 hover:text-gray-300 text-sm">← Paddocks</Link>
        </div>
        <div className="flex items-center gap-3 mt-2">
          <h2 className="text-2xl font-bold">{paddock.name}</h2>
          {paddock.is_world_paddock && (
            <span className="text-xs bg-blue-500/15 text-blue-400 border border-blue-500/20 rounded-full px-2.5 py-1">World</span>
          )}
        </div>
        <p className="text-gray-500 text-sm mt-1">
          {paddock.member_count} member{paddock.member_count !== 1 ? 's' : ''} · Join code: <span className="font-mono">{paddock.join_code}</span>
        </p>
      </div>

      {/* Action links */}
      <div className="flex gap-3 mb-6">
        <Link
          to={`/driver-predictions/${id}`}
          className="text-sm px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:text-white hover:border-white/20 transition-colors"
        >
          Driver standings pick
        </Link>
        <Link
          to={`/team-predictions/${id}`}
          className="text-sm px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:text-white hover:border-white/20 transition-colors"
        >
          Constructor standings pick
        </Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-white/10 mb-6">
        {['leaderboard', 'members'].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium capitalize transition-colors border-b-2 -mb-px ${
              tab === t
                ? 'text-white border-red-500'
                : 'text-gray-500 border-transparent hover:text-gray-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === 'leaderboard' && <LeaderboardTab rows={leaderboard} />}
      {tab === 'members' && <MembersTab members={paddock.members || []} />}
    </div>
  )
}

function LeaderboardTab({ rows }) {
  if (rows.length === 0) {
    return <p className="text-gray-500 text-sm">No scores yet — race results will appear here after scoring.</p>
  }

  return (
    <div className="space-y-2">
      {rows.map((row) => (
        <div key={row.user.id} className="flex items-center gap-4 px-5 py-3 rounded-xl border border-white/8 bg-white/4">
          <span className={`text-sm font-bold w-6 text-center ${row.rank === 1 ? 'text-yellow-400' : row.rank === 2 ? 'text-gray-300' : row.rank === 3 ? 'text-amber-600' : 'text-gray-600'}`}>
            {row.rank}
          </span>
          <div className="flex-1">
            <div className="text-sm font-medium text-white">{row.user.username}</div>
            <div className="text-xs text-gray-500">
              Pos {row.position_points}pt · Pole {row.pole_points}pt · FL {row.fastest_lap_points}pt · Quiz {row.quiz_points}pt
            </div>
          </div>
          <span className="text-lg font-bold text-white">{row.total}</span>
        </div>
      ))}
    </div>
  )
}

function MembersTab({ members }) {
  const roleOrder = { owner: 0, admin: 1, member: 2 }
  const sorted = [...members].sort((a, b) => (roleOrder[a.role] ?? 3) - (roleOrder[b.role] ?? 3))

  return (
    <div className="space-y-2">
      {sorted.map((m) => (
        <div key={m.id} className="flex items-center gap-3 px-5 py-3 rounded-xl border border-white/8 bg-white/4">
          <div className="flex-1 text-sm text-white">{m.username}</div>
          <span className={`text-xs px-2 py-0.5 rounded-full border ${
            m.role === 'owner' ? 'bg-red-500/15 text-red-400 border-red-500/20' :
            m.role === 'admin' ? 'bg-blue-500/15 text-blue-400 border-blue-500/20' :
            'bg-white/5 text-gray-500 border-white/10'
          }`}>
            {m.role}
          </span>
        </div>
      ))}
    </div>
  )
}
