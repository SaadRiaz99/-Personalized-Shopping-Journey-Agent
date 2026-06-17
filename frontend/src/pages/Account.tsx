import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { authChangePassword, authGetHistory, authGetSessions, authRevokeSession } from '../services/api'
import type { LoginHistoryEntry, UserSession } from '../types'

export default function Account() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [pwdMsg, setPwdMsg] = useState('')
  const [history, setHistory] = useState<LoginHistoryEntry[]>([])
  const [sessions, setSessions] = useState<UserSession[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [showSessions, setShowSessions] = useState(false)

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setPwdMsg('')
    try {
      await authChangePassword(currentPassword, newPassword)
      setPwdMsg('Password changed successfully')
      setCurrentPassword('')
      setNewPassword('')
    } catch {
      setPwdMsg('Failed to change password')
    }
  }

  const loadHistory = async () => {
    setShowHistory(!showHistory)
    if (!showHistory) {
      try {
        const res = await authGetHistory()
        setHistory(res.entries)
      } catch { /* ignore */ }
    }
  }

  const loadSessions = async () => {
    setShowSessions(!showSessions)
    if (!showSessions) {
      try {
        const res = await authGetSessions()
        setSessions(res.sessions)
      } catch { /* ignore */ }
    }
  }

  const revokeSession = async (id: string) => {
    try {
      await authRevokeSession(id)
      setSessions(prev => prev.filter(s => s.id !== id))
    } catch { /* ignore */ }
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <div className="account-page">
      <h2>Account Settings</h2>

      <div className="account-section">
        <h3>Profile</h3>
        <div className="profile-info">
          <div><span className="label">Username:</span> {user?.username}</div>
          <div><span className="label">Email:</span> {user?.email}</div>
          <div><span className="label">Role:</span> <span className={`role-badge ${user?.role}`}>{user?.role}</span></div>
        </div>
      </div>

      <div className="account-section">
        <h3>Change Password</h3>
        <form onSubmit={handlePasswordChange} className="password-form">
          <input type="password" placeholder="Current password" value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} required />
          <input type="password" placeholder="New password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required />
          <button type="submit" className="btn btn-primary">Update Password</button>
          {pwdMsg && <div className={pwdMsg.includes('success') ? 'success-msg' : 'error-msg'}>{pwdMsg}</div>}
        </form>
      </div>

      <div className="account-section">
        <button className="btn btn-ghost" onClick={loadHistory}>
          {showHistory ? 'Hide' : 'Show'} Login History
        </button>
        {showHistory && (
          <div className="history-list">
            {history.map(entry => (
              <div key={entry.id} className="history-item">
                <span className={entry.success ? 'text-success' : 'text-danger'}>
                  {entry.success ? '✓' : '✗'}
                </span>
                <span>{entry.ip_address}</span>
                <span className="text-dim">{new Date(entry.timestamp).toLocaleString()}</span>
                {entry.fail_reason && <span className="text-dim">{entry.fail_reason}</span>}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="account-section">
        <button className="btn btn-ghost" onClick={loadSessions}>
          {showSessions ? 'Hide' : 'Show'} Active Sessions
        </button>
        {showSessions && (
          <div className="session-list">
            {sessions.map(session => (
              <div key={session.id} className="session-item">
                <span>{session.device_info}</span>
                <span className="text-dim">{session.ip_address}</span>
                <button className="btn btn-danger-sm" onClick={() => revokeSession(session.id)}>Revoke</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="account-section">
        <button className="btn btn-danger" onClick={handleLogout}>Logout</button>
      </div>

      <style>{`
        .account-page { max-width: 600px; margin: 0 auto; }
        .account-page h2 { margin-bottom: 24px; }
        .account-section { margin-bottom: 24px; padding: 20px; border-radius: 16px; background: var(--glass-card); border: 1px solid var(--glass-border); }
        .account-section h3 { margin-bottom: 12px; }
        .profile-info { display: flex; flex-direction: column; gap: 8px; font-size: 0.95rem; }
        .profile-info .label { color: var(--text-dim); min-width: 80px; display: inline-block; }
        .password-form { display: flex; flex-direction: column; gap: 12px; }
        .password-form input { padding: 10px 14px; border-radius: 8px; border: 1px solid var(--glass-border); background: var(--bg); color: var(--text); font-size: 0.9rem; }
        .password-form input:focus { outline: none; border-color: var(--primary); }
        .btn-ghost { background: transparent; border: 1px solid var(--glass-border); color: var(--text); padding: 10px 16px; border-radius: 8px; cursor: pointer; transition: var(--transition-smooth); }
        .btn-ghost:hover { background: var(--glass-highlight); }
        .btn-danger { background: rgba(239,68,68,0.1); border: 1px solid var(--danger); color: var(--danger); padding: 10px 20px; border-radius: 8px; cursor: pointer; }
        .btn-danger-sm { background: rgba(239,68,68,0.1); border: 1px solid var(--danger); color: var(--danger); padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 0.8rem; }
        .role-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
        .role-badge.admin { background: rgba(99,102,241,0.2); color: #818cf8; }
        .role-badge.user { background: rgba(52,211,153,0.2); color: #34d399; }
        .success-msg { color: var(--success); font-size: 0.85rem; }
        .error-msg { color: var(--danger); font-size: 0.85rem; }
        .text-success { color: var(--success); }
        .text-danger { color: var(--danger); }
        .history-list, .session-list { margin-top: 12px; display: flex; flex-direction: column; gap: 8px; }
        .history-item, .session-item { display: flex; gap: 12px; align-items: center; padding: 8px; border-radius: 8px; background: rgba(255,255,255,0.02); font-size: 0.85rem; }
      `}</style>
    </div>
  )
}
