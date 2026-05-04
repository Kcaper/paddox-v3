import { useEffect, useState } from 'react'
import { f1Api } from '../api/f1'

export default function Dashboard() {
  const [races, setRaces] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    f1Api.races().then((r) => setRaces(r.data)).finally(() => setLoading(false))
  }, [])

  const now = new Date()
  const nextRaceIndex = races.findIndex((r) => !r.is_complete)

  return (
    <div className="max-w-3xl mx-auto px-6 py-8">
      <h2 className="text-2xl font-bold mb-1">2025 Season</h2>
      <p className="text-gray-500 text-sm mb-8">Formula 1 race calendar</p>

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-2">
          {races.map((race, idx) => (
            <RaceCard
              key={race.id}
              race={race}
              isNext={idx === nextRaceIndex}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function RaceCard({ race, isNext }) {
  const raceDate = race.race_at ? new Date(race.race_at) : null
  const qualiDate = race.quali_at ? new Date(race.quali_at) : null

  return (
    <div
      className={`rounded-xl border transition-colors ${
        race.is_complete
          ? 'border-white/5 bg-white/2 opacity-60'
          : isNext
          ? 'border-red-500/40 bg-red-500/5'
          : 'border-white/8 bg-white/4'
      }`}
    >
      <div className="flex items-center gap-4 px-5 py-4">
        {/* Round number */}
        <div className="w-8 text-center shrink-0">
          <span className={`text-xs font-mono font-bold ${race.is_complete ? 'text-gray-600' : 'text-gray-500'}`}>
            R{race.round}
          </span>
        </div>

        {/* Race info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`font-semibold text-sm ${race.is_complete ? 'text-gray-400' : 'text-white'}`}>
              {race.name}
            </span>
            {race.is_sprint_weekend && (
              <span className="text-xs bg-yellow-500/15 text-yellow-400 border border-yellow-500/20 rounded px-1.5 py-0.5">
                Sprint
              </span>
            )}
            {isNext && (
              <span className="text-xs bg-red-500/15 text-red-400 border border-red-500/20 rounded px-1.5 py-0.5">
                Next
              </span>
            )}
            {race.is_complete && (
              <span className="text-xs text-gray-600">Complete</span>
            )}
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            {race.circuit?.name} · {race.circuit?.country}
          </div>
        </div>

        {/* Dates */}
        <div className="text-right shrink-0 space-y-0.5">
          {qualiDate && (
            <div className="text-xs text-gray-500">
              Q {formatDate(qualiDate)}
            </div>
          )}
          {raceDate && (
            <div className={`text-xs font-medium ${race.is_complete ? 'text-gray-600' : 'text-gray-300'}`}>
              {formatDate(raceDate)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function formatDate(date) {
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
  })
}
