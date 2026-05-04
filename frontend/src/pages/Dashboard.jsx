import { useEffect, useState } from 'react'
import { f1Api } from '../api/f1'

export default function Dashboard() {
  const [races, setRaces] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    f1Api.races().then((r) => setRaces(r.data)).finally(() => setLoading(false))
  }, [])

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
  const [expanded, setExpanded] = useState(false)
  const [entries, setEntries] = useState(null)
  const [loadingEntries, setLoadingEntries] = useState(false)

  const raceDate = race.race_at ? new Date(race.race_at) : null
  const qualiDate = race.quali_at ? new Date(race.quali_at) : null

  const handleExpand = async () => {
    if (!race.is_complete) return
    if (!expanded && entries === null) {
      setLoadingEntries(true)
      try {
        const r = await f1Api.race(race.id)
        const sorted = (r.data.entries || [])
          .filter((e) => e.finish_position)
          .sort((a, b) => a.finish_position - b.finish_position)
        setEntries(sorted)
      } catch {
        setEntries([])
      } finally {
        setLoadingEntries(false)
      }
    }
    setExpanded((v) => !v)
  }

  return (
    <div
      className={`rounded-xl border transition-colors ${
        race.is_complete
          ? 'border-white/5 bg-white/2 opacity-70'
          : isNext
          ? 'border-red-500/40 bg-red-500/5'
          : 'border-white/8 bg-white/4'
      }`}
    >
      <div
        className={`flex items-center gap-4 px-5 py-4 ${race.is_complete ? 'cursor-pointer hover:opacity-100' : ''}`}
        onClick={handleExpand}
      >
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
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            {race.circuit?.name} · {race.circuit?.country}
          </div>
        </div>

        {/* Dates / expand hint */}
        <div className="text-right shrink-0 space-y-0.5">
          {race.is_complete ? (
            <span className="text-xs text-gray-600">{expanded ? '▲' : '▼'} results</span>
          ) : (
            <>
              {qualiDate && (
                <div className="text-xs text-gray-500">Q {formatDate(qualiDate)}</div>
              )}
              {raceDate && (
                <div className="text-xs font-medium text-gray-300">{formatDate(raceDate)}</div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Expandable results */}
      {expanded && (
        <div className="px-5 pb-4 border-t border-white/5 pt-3">
          {loadingEntries ? (
            <div className="flex justify-center py-4">
              <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : entries && entries.length > 0 ? (
            <div className="space-y-1.5">
              {entries.slice(0, 10).map((e) => (
                <div key={e.driver.id} className="flex items-center gap-3 text-xs">
                  <span className={`w-5 text-center font-bold shrink-0 ${
                    e.finish_position === 1 ? 'text-yellow-400' :
                    e.finish_position === 2 ? 'text-gray-300' :
                    e.finish_position === 3 ? 'text-amber-600' :
                    'text-gray-600'
                  }`}>
                    {e.finish_position}
                  </span>
                  <span className="text-gray-300 flex-1">
                    {e.driver.first_name} {e.driver.last_name}
                    {e.is_fastest_lap && <span className="ml-1.5 text-purple-400 font-medium">FL</span>}
                  </span>
                  <span className="text-gray-500">{e.driver.constructor?.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-600">No results available.</p>
          )}
        </div>
      )}
    </div>
  )
}

function formatDate(date) {
  return date.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
  })
}
