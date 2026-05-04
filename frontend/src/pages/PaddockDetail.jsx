import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { paddocksApi } from '../api/paddocks'
import { f1Api } from '../api/f1'

export default function PaddockDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [paddock, setPaddock] = useState(null)
  const [leaderboard, setLeaderboard] = useState([])
  const [seasonLeaderboard, setSeasonLeaderboard] = useState([])
  const [races, setRaces] = useState([])
  const [memberPicks, setMemberPicks] = useState(null)
  const [tab, setTab] = useState('leaderboard')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      paddocksApi.detail(id),
      paddocksApi.leaderboard(id),
      paddocksApi.seasonLeaderboard(id),
      f1Api.races(),
      paddocksApi.predictions(id),
    ]).then(([pd, lb, slb, rc, picks]) => {
      setPaddock(pd.data)
      setLeaderboard(lb.data.leaderboard || [])
      setSeasonLeaderboard(slb.data.leaderboard || [])
      setRaces((rc.data || []).filter((r) => r.is_complete))
      setMemberPicks(picks.data)
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
        {[['leaderboard', 'Racely'], ['season', 'Season'], ['picks', 'Picks'], ['members', 'Members']].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              tab === key
                ? 'text-white border-red-500'
                : 'text-gray-500 border-transparent hover:text-gray-300'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'leaderboard' && <LeaderboardTab paddockId={id} rows={leaderboard} completedRaces={races} />}
      {tab === 'season' && <SeasonLeaderboardTab rows={seasonLeaderboard} />}
      {tab === 'picks' && <PicksTab data={memberPicks} />}
      {tab === 'members' && (
        <MembersTab
          paddockId={id}
          members={paddock.members || []}
          myRole={paddock.my_role}
          currentUserId={user?.id}
          onUpdate={(updated) => setPaddock(updated)}
        />
      )}
    </div>
  )
}

function LeaderboardTab({ paddockId, rows, completedRaces }) {
  const [selectedRaceId, setSelectedRaceId] = useState(null)
  const [raceRows, setRaceRows] = useState([])
  const [raceLoading, setRaceLoading] = useState(false)

  useEffect(() => {
    if (!selectedRaceId) { setRaceRows([]); return }
    setRaceLoading(true)
    paddocksApi.raceLeaderboard(paddockId, selectedRaceId)
      .then((r) => setRaceRows(r.data.leaderboard || []))
      .catch(() => setRaceRows([]))
      .finally(() => setRaceLoading(false))
  }, [selectedRaceId, paddockId])

  const displayRows = selectedRaceId ? raceRows : rows
  const totalMode = !selectedRaceId

  return (
    <div className="space-y-4">
      {/* Race selector */}
      {completedRaces.length > 0 && (
        <div className="flex items-center gap-3">
          <select
            value={selectedRaceId || ''}
            onChange={(e) => setSelectedRaceId(e.target.value ? parseInt(e.target.value) : null)}
            className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-red-500/50"
          >
            <option value="">Season total</option>
            {completedRaces.map((r) => (
              <option key={r.id} value={r.id}>R{r.round} — {r.name}</option>
            ))}
          </select>
          {selectedRaceId && (
            <button onClick={() => setSelectedRaceId(null)} className="text-xs text-gray-500 hover:text-gray-300">
              ← Season total
            </button>
          )}
        </div>
      )}

      {raceLoading ? (
        <div className="flex justify-center py-8">
          <div className="w-5 h-5 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : displayRows.length === 0 ? (
        <p className="text-gray-500 text-sm">No scores yet — race results will appear here after scoring.</p>
      ) : (
        <div className="space-y-2">
          {displayRows.map((row) => (
            <div key={row.user.id} className="flex items-center gap-4 px-5 py-3 rounded-xl border border-white/8 bg-white/4">
              <span className={`text-sm font-bold w-6 text-center ${row.rank === 1 ? 'text-yellow-400' : row.rank === 2 ? 'text-gray-300' : row.rank === 3 ? 'text-amber-600' : 'text-gray-600'}`}>
                {row.rank}
              </span>
              <div className="flex-1">
                <div className="text-sm font-medium text-white">{row.user.username}</div>
                <div className="text-xs text-gray-500">
                  Pos {row.position_points}pt · Pole {row.pole_points}pt · FL {row.fastest_lap_points}pt
                  {totalMode ? ` · Quiz ${row.quiz_points}pt` : row.quiz_pending ? ' · Quiz pending' : ` · Quiz ${row.quiz_points}pt`}
                </div>
              </div>
              <span className="text-lg font-bold text-white">{row.total}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function PicksTab({ data }) {
  if (!data || !data.race) {
    return <p className="text-gray-500 text-sm">No locked race yet — picks become visible after qualifying.</p>
  }

  const { race, predictions } = data

  return (
    <div className="space-y-6">
      <p className="text-xs text-gray-500">
        R{race.round} {race.name} — all members' Racely picks
      </p>
      {predictions.map((p) => (
        <div key={p.user.id} className="bg-white/3 border border-white/8 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm font-semibold text-white">{p.user.username}</span>
            {p.is_rolled_over && (
              <span className="text-xs bg-blue-500/15 text-blue-400 border border-blue-500/20 rounded-full px-2 py-0.5">rolled over</span>
            )}
            {p.entries.length === 0 && (
              <span className="text-xs text-gray-600">no prediction</span>
            )}
          </div>

          {p.entries.length > 0 && (
            <div className="grid grid-cols-2 gap-x-6 gap-y-1">
              {p.entries.map((e) => (
                <div key={e.position} className="flex items-center gap-2 text-xs">
                  <span className="text-red-400 font-mono w-4 shrink-0">{e.position}</span>
                  <span className="text-gray-300">{e.driver.last_name}</span>
                  <span className="text-gray-600 text-[10px]">{e.driver.constructor?.name}</span>
                </div>
              ))}
            </div>
          )}

          {(p.pole || p.fastest_lap) && (
            <div className="flex gap-4 mt-3 pt-3 border-t border-white/5 text-xs text-gray-500">
              {p.pole && <span>Pole: <span className="text-gray-300">{p.pole.last_name}</span></span>}
              {p.fastest_lap && <span>FL: <span className="text-gray-300">{p.fastest_lap.last_name}</span></span>}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function SeasonLeaderboardTab({ rows }) {
  if (rows.length === 0) {
    return <p className="text-gray-500 text-sm">No season scores yet — standings predictions will be scored after each race.</p>
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
              Drivers {row.driver_points}pt · Constructors {row.constructor_points}pt
            </div>
          </div>
          <span className="text-lg font-bold text-white">{row.total}</span>
        </div>
      ))}
    </div>
  )
}

function MembersTab({ paddockId, members, myRole, currentUserId, onUpdate }) {
  const [busy, setBusy] = useState(null)
  const roleOrder = { owner: 0, admin: 1, member: 2 }
  const sorted = [...members].sort((a, b) => (roleOrder[a.role] ?? 3) - (roleOrder[b.role] ?? 3))

  const canManage = myRole === 'owner' || myRole === 'admin'

  async function handleRole(memberId, newRole) {
    setBusy(memberId)
    try {
      const res = await paddocksApi.updateMemberRole(paddockId, memberId, newRole)
      onUpdate(res.data)
    } catch {
      // ignore
    } finally {
      setBusy(null)
    }
  }

  async function handleRemove(memberId) {
    if (!confirm('Remove this member from the paddock?')) return
    setBusy(memberId)
    try {
      const res = await paddocksApi.removeMember(paddockId, memberId)
      onUpdate(res.data)
    } catch {
      // ignore
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="space-y-2">
      {sorted.map((m) => {
        const isMe = m.id === currentUserId
        const isBusy = busy === m.id
        const showControls = canManage && !isMe && m.role !== 'owner'

        return (
          <div key={m.id} className="flex items-center gap-3 px-5 py-3 rounded-xl border border-white/8 bg-white/4">
            <div className="flex-1 text-sm text-white">{m.username}{isMe && <span className="text-gray-500 ml-1">(you)</span>}</div>
            <span className={`text-xs px-2 py-0.5 rounded-full border ${
              m.role === 'owner' ? 'bg-red-500/15 text-red-400 border-red-500/20' :
              m.role === 'admin' ? 'bg-blue-500/15 text-blue-400 border-blue-500/20' :
              'bg-white/5 text-gray-500 border-white/10'
            }`}>
              {m.role}
            </span>
            {showControls && (
              <div className="flex items-center gap-2">
                {myRole === 'owner' && (
                  <button
                    disabled={isBusy}
                    onClick={() => handleRole(m.id, m.role === 'admin' ? 'member' : 'admin')}
                    className="text-xs text-gray-500 hover:text-blue-400 transition-colors disabled:opacity-40"
                  >
                    {m.role === 'admin' ? 'Demote' : 'Make admin'}
                  </button>
                )}
                <button
                  disabled={isBusy}
                  onClick={() => handleRemove(m.id)}
                  className="text-xs text-gray-500 hover:text-red-400 transition-colors disabled:opacity-40"
                >
                  Remove
                </button>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
