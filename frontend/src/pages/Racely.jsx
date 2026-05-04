import { useEffect, useState, useCallback } from 'react'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core'
import {
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { predictionsApi } from '../api/predictions'

export default function Racely() {
  const [state, setState] = useState(null)
  const [ordered, setOrdered] = useState([])        // driver objects in predicted order
  const [poolDrivers, setPoolDrivers] = useState([]) // remaining drivers not yet picked
  const [poleDriver, setPoleDriver] = useState(null)
  const [flDriver, setFlDriver] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    predictionsApi.racelyCurrentState().then((r) => {
      const data = r.data
      setState(data)

      const available = data.available_drivers || []
      const existing = data.prediction?.entries || []

      if (existing.length > 0) {
        // Restore existing prediction order
        const pickedIds = new Set(existing.map((e) => e.driver.id))
        setOrdered(existing.map((e) => e.driver))
        setPoolDrivers(available.filter((d) => !pickedIds.has(d.id)))
      } else {
        setOrdered([])
        setPoolDrivers(available)
      }

      if (data.pole_prediction?.driver) setPoleDriver(data.pole_prediction.driver)
      if (data.fastest_lap_prediction?.driver) setFlDriver(data.fastest_lap_prediction.driver)
    }).finally(() => setLoading(false))
  }, [])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragEnd = (event) => {
    const { active, over } = event
    if (!over || active.id === over.id) return
    setOrdered((prev) => {
      const oldIdx = prev.findIndex((d) => d.id === active.id)
      const newIdx = prev.findIndex((d) => d.id === over.id)
      return arrayMove(prev, oldIdx, newIdx)
    })
  }

  const addDriver = (driver) => {
    setOrdered((prev) => [...prev, driver])
    setPoolDrivers((prev) => prev.filter((d) => d.id !== driver.id))
  }

  const removeDriver = (driver) => {
    setOrdered((prev) => prev.filter((d) => d.id !== driver.id))
    setPoolDrivers((prev) => [...prev, driver].sort((a, b) => a.last_name.localeCompare(b.last_name)))
  }

  const handleSave = async () => {
    if (ordered.length === 0) {
      setError('Pick at least one driver.')
      return
    }
    setSaving(true)
    setError('')
    try {
      await predictionsApi.submitRacely(
        ordered.map((d) => d.id),
        poleDriver?.id ?? null,
        flDriver?.id ?? null,
      )
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save prediction.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!state) return <div className="p-8 text-gray-500">No active race found.</div>

  const race = state.race
  const locked = state.deadline_passed
  const noPrediction = !state.prediction && locked

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-1 flex-wrap">
          <h2 className="text-2xl font-bold">Racely</h2>
          {locked && (
            <span className="text-xs bg-yellow-500/15 text-yellow-400 border border-yellow-500/20 rounded-full px-3 py-1">
              Deadline passed — view only
            </span>
          )}
          {state.prediction?.is_rolled_over && (
            <span className="text-xs bg-blue-500/15 text-blue-400 border border-blue-500/20 rounded-full px-3 py-1">
              Rolled over from last race
            </span>
          )}
        </div>
        <p className="text-gray-500 text-sm">
          {race.name} · {race.circuit?.country}
          {race.quali_at && !locked && (
            <> · Deadline: {new Date(race.quali_at).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZoneName: 'short' })}</>
          )}
        </p>
      </div>

      {noPrediction && (
        <div className="mb-6 px-4 py-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-sm">
          You didn't submit a prediction before the deadline. Your last race's prediction will be rolled over for scoring.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Ordered prediction list */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">Your picks (drag to reorder)</h3>
            <span className="text-xs text-gray-500">{ordered.length} drivers</span>
          </div>

          {ordered.length === 0 ? (
            <div className="border border-dashed border-white/10 rounded-xl p-8 text-center text-gray-600 text-sm">
              Add drivers from the right →
            </div>
          ) : (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={ordered.map((d) => d.id)} strategy={verticalListSortingStrategy}>
                <div className="space-y-1.5">
                  {ordered.map((driver, idx) => (
                    <SortableDriver
                      key={driver.id}
                      driver={driver}
                      position={idx + 1}
                      locked={locked}
                      onRemove={() => removeDriver(driver)}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          )}

          {/* Bonus picks */}
          <div className="mt-6 space-y-3">
            <BonusPicker
              label="Pole Position"
              value={poleDriver}
              options={state.available_drivers}
              locked={locked}
              onChange={setPoleDriver}
            />
            <BonusPicker
              label="Fastest Lap"
              value={flDriver}
              options={state.available_drivers}
              locked={locked}
              onChange={setFlDriver}
            />
          </div>

          {/* Save */}
          {!locked && (
            <div className="mt-6">
              {error && <p className="text-sm text-red-400 mb-3">{error}</p>}
              <button
                onClick={handleSave}
                disabled={saving}
                className="w-full bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
              >
                {saving ? 'Saving…' : saved ? '✓ Saved' : 'Save prediction'}
              </button>
            </div>
          )}
        </div>

        {/* Right: Driver pool */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">Available drivers</h3>
            <span className="text-xs text-gray-500">{poolDrivers.length} remaining</span>
          </div>

          <div className="space-y-1.5 max-h-[32rem] overflow-y-auto pr-1">
            {poolDrivers.map((driver) => (
              <button
                key={driver.id}
                disabled={locked}
                onClick={() => addDriver(driver)}
                className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg bg-white/4 hover:bg-white/8 disabled:opacity-40 disabled:cursor-default border border-white/5 text-left transition-colors"
              >
                <span className="text-xs font-mono text-gray-500 w-8 shrink-0">{driver.abbreviation}</span>
                <span className="text-sm text-white flex-1">{driver.first_name} {driver.last_name}</span>
                <span className="text-xs text-gray-500 shrink-0">{driver.constructor?.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function SortableDriver({ driver, position, locked, onRemove }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: driver.id,
    disabled: locked,
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 50 : undefined,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border ${
        isDragging ? 'border-red-500/40 bg-red-500/5' : 'border-white/8 bg-white/4'
      }`}
    >
      {/* Position badge */}
      <span className="text-xs font-mono text-red-400 w-6 shrink-0 text-center">{position}</span>

      {/* Driver info */}
      <div className="flex-1 min-w-0">
        <div className="text-sm text-white">{driver.first_name} {driver.last_name}</div>
        <div className="text-xs text-gray-500">{driver.constructor?.name}</div>
      </div>

      {/* Abbreviation */}
      <span className="text-xs font-mono text-gray-500">{driver.abbreviation}</span>

      {/* Drag handle */}
      {!locked && (
        <button
          {...attributes}
          {...listeners}
          className="text-gray-600 hover:text-gray-400 cursor-grab active:cursor-grabbing p-1 touch-none"
          aria-label="Drag to reorder"
        >
          <GripIcon />
        </button>
      )}

      {/* Remove */}
      {!locked && (
        <button
          onClick={onRemove}
          className="text-gray-600 hover:text-red-400 transition-colors p-1"
          aria-label="Remove"
        >
          ×
        </button>
      )}
    </div>
  )
}

function BonusPicker({ label, value, options, locked, onChange }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label} (+1 pt)</label>
      <select
        value={value?.id ?? ''}
        disabled={locked}
        onChange={(e) => {
          const selected = options.find((d) => d.id === parseInt(e.target.value))
          onChange(selected || null)
        }}
        className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white disabled:opacity-40 focus:outline-none focus:border-red-500/50"
      >
        <option value="">— Pick a driver —</option>
        {options.map((d) => (
          <option key={d.id} value={d.id}>
            {d.last_name}, {d.first_name} ({d.abbreviation})
          </option>
        ))}
      </select>
    </div>
  )
}

function GripIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
      <rect x="3" y="2" width="2" height="2" rx="1" />
      <rect x="9" y="2" width="2" height="2" rx="1" />
      <rect x="3" y="6" width="2" height="2" rx="1" />
      <rect x="9" y="6" width="2" height="2" rx="1" />
      <rect x="3" y="10" width="2" height="2" rx="1" />
      <rect x="9" y="10" width="2" height="2" rx="1" />
    </svg>
  )
}
