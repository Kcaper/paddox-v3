import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { authApi } from '../api/auth'

export default function Profile() {
  const { user, setUser } = useAuth()

  const [username, setUsername] = useState(user?.username || '')
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '')
  const [profileMsg, setProfileMsg] = useState(null)
  const [profileError, setProfileError] = useState(null)
  const [profileSaving, setProfileSaving] = useState(false)

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [pwMsg, setPwMsg] = useState(null)
  const [pwError, setPwError] = useState(null)
  const [pwSaving, setPwSaving] = useState(false)

  async function handleProfileSave(e) {
    e.preventDefault()
    setProfileMsg(null)
    setProfileError(null)
    setProfileSaving(true)
    try {
      const res = await authApi.updateProfile({ username, avatar_url: avatarUrl })
      setUser(res.data)
      setProfileMsg('Profile updated.')
    } catch (err) {
      setProfileError(err.response?.data?.username?.[0] || err.response?.data?.detail || 'Failed to save.')
    } finally {
      setProfileSaving(false)
    }
  }

  async function handlePasswordChange(e) {
    e.preventDefault()
    setPwMsg(null)
    setPwError(null)
    if (newPw !== confirmPw) {
      setPwError('Passwords do not match.')
      return
    }
    if (newPw.length < 8) {
      setPwError('Password must be at least 8 characters.')
      return
    }
    setPwSaving(true)
    try {
      await authApi.changePassword(currentPw, newPw)
      setPwMsg('Password changed.')
      setCurrentPw('')
      setNewPw('')
      setConfirmPw('')
    } catch (err) {
      setPwError(err.response?.data?.detail || 'Failed to change password.')
    } finally {
      setPwSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-lg mx-auto space-y-8">
      <h1 className="text-2xl font-bold text-white">Profile</h1>

      {/* Avatar preview */}
      {avatarUrl && (
        <div className="flex justify-center">
          <img
            src={avatarUrl}
            alt="Avatar"
            className="w-20 h-20 rounded-full object-cover border-2 border-white/10"
            onError={(e) => { e.target.style.display = 'none' }}
          />
        </div>
      )}

      {/* Profile form */}
      <section className="bg-[#1a1a26] rounded-xl p-6 border border-white/10 space-y-4">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Account</h2>
        <form onSubmit={handleProfileSave} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Email</label>
            <input
              value={user?.email || ''}
              disabled
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-500 cursor-not-allowed"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Avatar URL</label>
            <input
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              placeholder="https://..."
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-red-500/50"
            />
          </div>
          {profileError && <p className="text-red-400 text-sm">{profileError}</p>}
          {profileMsg && <p className="text-green-400 text-sm">{profileMsg}</p>}
          <button
            type="submit"
            disabled={profileSaving}
            className="bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {profileSaving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      </section>

      {/* Password form */}
      <section className="bg-[#1a1a26] rounded-xl p-6 border border-white/10 space-y-4">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Change Password</h2>
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Current password</label>
            <input
              type="password"
              value={currentPw}
              onChange={(e) => setCurrentPw(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">New password</label>
            <input
              type="password"
              value={newPw}
              onChange={(e) => setNewPw(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Confirm new password</label>
            <input
              type="password"
              value={confirmPw}
              onChange={(e) => setConfirmPw(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500/50"
            />
          </div>
          {pwError && <p className="text-red-400 text-sm">{pwError}</p>}
          {pwMsg && <p className="text-green-400 text-sm">{pwMsg}</p>}
          <button
            type="submit"
            disabled={pwSaving}
            className="bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {pwSaving ? 'Saving…' : 'Change password'}
          </button>
        </form>
      </section>
    </div>
  )
}
