import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  DndContext, closestCenter, KeyboardSensor, PointerSensor,
  useSensor, useSensors,
} from '@dnd-kit/core'
import {
  SortableContext, sortableKeyboardCoordinates, useSortable,
  verticalListSortingStrategy, arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import client from '../api/client'
import { f1Api } from '../api/f1'

export default function SeasonPredictions() {
  const { paddockId } = useParams()
  const isDrivers = window.location.pathname.includes('driver-predictions')

  const [state, setState] = useState(null)
  const [ordered, setOrdered] = useState([])
  const [pool, setPool] = useState([])
  const [standings, setStandings] = useState({}) // id → current position
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const itemKey = isDrivers ? 'driver' : 'constructor'
  const idKey = isDrivers ? 'driver_ids' : 'constructor_ids'
  const submitUrl = isDrivers
    ? `/api/predictions/season/${paddockId}/drivers/`
    : `/api/predictions/season/${paddockId}/constructors/`

  useEffect(() => {
    const standingsFetch = isDrivers ? f1Api.driverStandings() : f1Api.constructorStandings()
    Promise.all([
      client.get(`/api/predictions/season/${paddockId}/`),
      standingsFetch,
    ]).then(([predRes, standRes]) => {
      const data = predRes.data
      setState(data)

      const available = isDrivers ? data.available_drivers : data.available_constructors
      const existing = isDrivers ? data.driver_prediction : data.constructor_prediction

      if (existing.length > 0) {
        const pickedIds = new Set(existing.map((e) => e[itemKey].id))
        setOrdered(existing.map((e) => e[itemKey]))
        setPool(available.filter((d) => !pickedIds.has(d.id)))
      } else {
        setOrdered([])
        setPool(available)
      }

      const standMap = {}
      for (const s of (standRes.data || [])) {
        const id = isDrivers ? s.driver?.id : s.constructor?.id
        if (id) standMap[id] = s.position
      }
      setStandings(standMap)
    }).finally(() => setLoading(false))
  }, [paddockId, isDrivers])

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const handleDragEnd = ({ active, over }) => {
    if (!over || active.id === over.id) return
    setOrdered((prev) => {
      const oldIdx = prev.findIndex((d) => d.id === active.id)
      const newIdx = prev.findIndex((d) => d.id === over.id)
      return arrayMove(prev, oldIdx, newIdx)
    })
  }

  const addItem = (item) => {
    setOrdered((prev) => [...prev, item])
    setPool((prev) => prev.filter((d) => d.id !== item.id))
  }

  const removeItem = (item) => {
    setOrdered((prev) => prev.filter((d) => d.id !== item.id))
    setPool((prev) => [...prev, item].sort((a, b) => (a.last_name || a.name).localeCompare(b.last_name || b.name)))
  }

  const handleSave = async () => {
    if (ordered.length === 0) { setError('Pick at least one.'); return }
    setSaving(true); setError('')
    try {
      await client.post(submitUrl, { [idKey]: ordered.map((d) => d.id) })
      setSaved(true); setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save.')
    } finally { setSaving(false) }
  }

  const locked = state?.deadline_passed

  if (loading) return (
    <div className="flex justify-center py-20">
      <div className="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )

  const title = isDrivers ? 'Driver Championship' : 'Constructor Championship'
  const backUrl = `/paddock/${paddockId}`

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <div className="mb-6">
        <Link to={backUrl} className="text-gray-500 hover:text-gray-300 text-sm">← Back to paddock</Link>
        <div className="flex items-center gap-3 mt-2">
          <h2 className="text-2xl font-bold">{title} Prediction</h2>
          {locked && (
            <span className="text-xs bg-yellow-500/15 text-yellow-400 border border-yellow-500/20 rounded-full px-3 py-1">
              Deadline passed — view only
            </span>
          )}
        </div>
        <p className="text-gray-500 text-sm mt-1">
          Predict the final {isDrivers ? 'driver' : 'constructor'} championship order for the season.
          Scored after each race (exact=2pts, off by 1=1pt).
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ordered picks */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">Your prediction</h3>
            <span className="text-xs text-gray-500">{ordered.length} picked</span>
          </div>
          {ordered.length === 0 ? (
            <div className="border border-dashed border-white/10 rounded-xl p-8 text-center text-gray-600 text-sm">
              Add {isDrivers ? 'drivers' : 'constructors'} from the right →
            </div>
          ) : (
            <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
              <SortableContext items={ordered.map((d) => d.id)} strategy={verticalListSortingStrategy}>
                <div className="space-y-1.5">
                  {ordered.map((item, idx) => (
                    <SortableItem
                      key={item.id}
                      item={item}
                      position={idx + 1}
                      isDriver={isDrivers}
                      locked={locked}
                      onRemove={() => removeItem(item)}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          )}
          {!locked && (
            <div className="mt-5">
              {error && <p className="text-sm text-red-400 mb-2">{error}</p>}
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

        {/* Pool */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-300">
              {isDrivers ? 'Available drivers' : 'Available constructors'}
            </h3>
            <span className="text-xs text-gray-500">{pool.length} remaining</span>
          </div>
          {Object.keys(standings).length > 0 && (
            <p className="text-xs text-gray-600 mb-2">P# = current championship position</p>
          )}
          <div className="space-y-1.5 max-h-[32rem] overflow-y-auto pr-1">
            {pool.map((item) => {
              const currentPos = standings[item.id]
              return (
                <button
                  key={item.id}
                  disabled={locked}
                  onClick={() => addItem(item)}
                  className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg bg-white/4 hover:bg-white/8 disabled:opacity-40 border border-white/5 text-left transition-colors"
                >
                  {currentPos && (
                    <span className="text-xs font-mono text-gray-600 w-5 shrink-0">P{currentPos}</span>
                  )}
                  {isDrivers ? (
                    <>
                      <span className="text-xs font-mono text-gray-500 w-8 shrink-0">{item.abbreviation}</span>
                      <span className="text-sm text-white flex-1">{item.first_name} {item.last_name}</span>
                      <span className="text-xs text-gray-500">{item.constructor?.name}</span>
                    </>
                  ) : (
                    <span className="text-sm text-white flex-1">{item.name}</span>
                  )}
                </button>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

function SortableItem({ item, position, isDriver, locked, onRemove }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.id, disabled: locked,
  })
  const style = { transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 }

  return (
    <div ref={setNodeRef} style={style}
      className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border ${isDragging ? 'border-red-500/40 bg-red-500/5' : 'border-white/8 bg-white/4'}`}
    >
      <span className="text-xs font-mono text-red-400 w-6 text-center">{position}</span>
      <div className="flex-1 min-w-0">
        {isDriver ? (
          <>
            <div className="text-sm text-white">{item.first_name} {item.last_name}</div>
            <div className="text-xs text-gray-500">{item.constructor?.name}</div>
          </>
        ) : (
          <div className="text-sm text-white">{item.name}</div>
        )}
      </div>
      {!locked && (
        <>
          <button {...attributes} {...listeners} className="text-gray-600 hover:text-gray-400 cursor-grab p-1 touch-none">
            <GripIcon />
          </button>
          <button onClick={onRemove} className="text-gray-600 hover:text-red-400 transition-colors p-1">×</button>
        </>
      )}
    </div>
  )
}

function GripIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
      <rect x="3" y="2" width="2" height="2" rx="1" /><rect x="9" y="2" width="2" height="2" rx="1" />
      <rect x="3" y="6" width="2" height="2" rx="1" /><rect x="9" y="6" width="2" height="2" rx="1" />
      <rect x="3" y="10" width="2" height="2" rx="1" /><rect x="9" y="10" width="2" height="2" rx="1" />
    </svg>
  )
}
