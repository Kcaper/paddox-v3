import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { paddocksApi } from '../api/paddocks'

export default function MyPaddocks() {
  const [paddocks, setPaddocks] = useState([])
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState('list') // 'list' | 'create' | 'join'

  const reload = () => {
    paddocksApi.list().then((r) => setPaddocks(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { reload() }, [])

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">My Paddocks</h2>
          <p className="text-gray-500 text-sm mt-0.5">Groups you predict in together</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setView(view === 'join' ? 'list' : 'join')}
            className="text-sm px-4 py-2 rounded-lg border border-white/10 text-gray-300 hover:text-white hover:border-white/20 transition-colors"
          >
            Join
          </button>
          <button
            onClick={() => setView(view === 'create' ? 'list' : 'create')}
            className="text-sm px-4 py-2 rounded-lg bg-red-500 hover:bg-red-600 text-white transition-colors"
          >
            + Create
          </button>
        </div>
      </div>

      {view === 'create' && (
        <CreatePaddockForm onSuccess={() => { setView('list'); reload() }} />
      )}
      {view === 'join' && (
        <JoinPaddockForm onSuccess={() => { setView('list'); reload() }} />
      )}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-3 mt-4">
          {paddocks.map((p) => (
            <PaddockCard key={p.id} paddock={p} />
          ))}
        </div>
      )}
    </div>
  )
}

function PaddockCard({ paddock }) {
  return (
    <Link
      to={`/paddock/${paddock.id}`}
      className="flex items-center gap-4 px-5 py-4 rounded-xl border border-white/8 bg-white/4 hover:bg-white/7 hover:border-white/15 transition-colors block"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white text-sm">{paddock.name}</span>
          {paddock.is_world_paddock && (
            <span className="text-xs bg-blue-500/15 text-blue-400 border border-blue-500/20 rounded px-1.5 py-0.5">World</span>
          )}
          {paddock.is_public && !paddock.is_world_paddock && (
            <span className="text-xs bg-green-500/15 text-green-400 border border-green-500/20 rounded px-1.5 py-0.5">Public</span>
          )}
        </div>
        <div className="text-xs text-gray-500 mt-0.5">
          {paddock.member_count} member{paddock.member_count !== 1 ? 's' : ''} · {paddock.my_role}
        </div>
      </div>
      <div className="text-xs font-mono text-gray-600">{paddock.join_code}</div>
    </Link>
  )
}

function CreatePaddockForm({ onSuccess }) {
  const [form, setForm] = useState({ name: '', is_public: false, max_players: 20, racely_scoring_positions: 10 })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await paddocksApi.create(form)
      onSuccess()
    } catch (err) {
      const d = err.response?.data
      setError(typeof d === 'string' ? d : d?.detail || JSON.stringify(d) || 'Failed to create.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white/4 border border-white/8 rounded-xl p-5 mb-4 space-y-4">
      <h3 className="font-semibold text-sm">Create a paddock</h3>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <div>
        <label className="block text-xs text-gray-400 mb-1">Name</label>
        <input
          required
          maxLength={30}
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50"
          placeholder="The Grid"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Max players</label>
          <input
            type="number" min={2} max={500}
            value={form.max_players}
            onChange={(e) => setForm({ ...form, max_players: parseInt(e.target.value) })}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Scoring positions</label>
          <input
            type="number" min={1} max={20}
            value={form.racely_scoring_positions}
            onChange={(e) => setForm({ ...form, racely_scoring_positions: parseInt(e.target.value) })}
            className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50"
          />
        </div>
      </div>

      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={form.is_public}
          onChange={(e) => setForm({ ...form, is_public: e.target.checked })}
          className="accent-red-500"
        />
        <span className="text-sm text-gray-300">Public paddock (visible to anyone)</span>
      </label>

      <button
        type="submit"
        disabled={loading}
        className="w-full bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-medium py-2 rounded-lg text-sm transition-colors"
      >
        {loading ? 'Creating…' : 'Create paddock'}
      </button>
    </form>
  )
}

function JoinPaddockForm({ onSuccess }) {
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await paddocksApi.join(code.trim().toUpperCase())
      onSuccess()
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid join code.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white/4 border border-white/8 rounded-xl p-5 mb-4 flex gap-3">
      <input
        required
        maxLength={6}
        value={code}
        onChange={(e) => setCode(e.target.value.toUpperCase())}
        className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white font-mono uppercase tracking-widest focus:outline-none focus:border-red-500/50"
        placeholder="ABC123"
      />
      <button
        type="submit"
        disabled={loading}
        className="bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-colors"
      >
        {loading ? '…' : 'Join'}
      </button>
      {error && <p className="text-sm text-red-400 self-center">{error}</p>}
    </form>
  )
}
