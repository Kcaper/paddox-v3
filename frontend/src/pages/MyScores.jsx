import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { paddocksApi } from '../api/paddocks'

export default function MyScores() {
  const [races, setRaces] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    paddocksApi.myScores().then((r) => setRaces(r.data.races || [])).finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  const totalByPaddock = {}
  for (const race of races) {
    for (const p of race.paddocks) {
      if (!totalByPaddock[p.paddock_id]) {
        totalByPaddock[p.paddock_id] = { name: p.paddock_name, total: 0 }
      }
      totalByPaddock[p.paddock_id].total += p.total
    }
  }
  const paddockTotals = Object.values(totalByPaddock)

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h2 className="text-2xl font-bold mb-1">My Scores</h2>
      <p className="text-gray-500 text-sm mb-6">Your Racely points, race by race</p>

      {races.length === 0 ? (
        <p className="text-gray-500 text-sm">No scores yet — race results will appear here after scoring.</p>
      ) : (
        <>
          {/* Season totals */}
          {paddockTotals.length > 0 && (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8">
              {paddockTotals.map((p) => (
                <div key={p.name} className="bg-white/4 border border-white/8 rounded-xl px-4 py-3 text-center">
                  <div className="text-2xl font-bold text-white">{p.total}</div>
                  <div className="text-xs text-gray-500 mt-0.5 truncate">{p.name}</div>
                </div>
              ))}
            </div>
          )}

          {/* Per-race rows */}
          <div className="space-y-3">
            {[...races].reverse().map((race) => (
              <RaceRow key={race.id} race={race} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function RaceRow({ race }) {
  const [expanded, setExpanded] = useState(false)

  const bestTotal = Math.max(...race.paddocks.map((p) => p.total))

  return (
    <div className="rounded-xl border border-white/8 bg-white/3 overflow-hidden">
      <button
        className="w-full flex items-center gap-4 px-5 py-3 text-left hover:bg-white/3 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <span className="text-xs font-mono text-gray-600 shrink-0 w-6">R{race.round}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-white">{race.name}</span>
            {race.is_rolled_over && (
              <span className="text-xs bg-blue-500/15 text-blue-400 border border-blue-500/20 rounded-full px-2 py-0.5">
                rolled over
              </span>
            )}
          </div>
          <div className="text-xs text-gray-500">{race.circuit} · {race.country}</div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-lg font-bold text-white">{bestTotal}<span className="text-xs text-gray-600 font-normal">pt</span></div>
          <div className="text-[10px] text-gray-600">{expanded ? '▲' : '▼'}</div>
        </div>
      </button>

      {expanded && (
        <div className="border-t border-white/5 px-5 py-3 space-y-3">
          {race.paddocks.map((p) => (
            <div key={p.paddock_id}>
              <div className="flex items-center justify-between mb-1.5">
                <Link
                  to={`/paddock/${p.paddock_id}`}
                  className="text-xs font-medium text-gray-300 hover:text-white transition-colors"
                >
                  {p.paddock_name} →
                </Link>
                <span className="text-sm font-bold text-white">{p.total}pt</span>
              </div>
              <div className="flex gap-3">
                <ScorePill label="Position" value={p.position_points} />
                <ScorePill label="Pole" value={p.pole_points} />
                <ScorePill label="FL" value={p.fastest_lap_points} />
                <ScorePill
                  label="Quiz"
                  value={p.quiz_points}
                  pending={p.quiz_pending}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ScorePill({ label, value, pending }) {
  return (
    <div className="flex-1 bg-white/4 rounded-lg px-2 py-1.5 text-center">
      <div className={`text-sm font-bold ${value > 0 ? 'text-white' : 'text-gray-600'}`}>
        {pending ? <span className="text-yellow-500/70 text-xs">?</span> : value}
      </div>
      <div className="text-[10px] text-gray-600">{label}</div>
    </div>
  )
}
