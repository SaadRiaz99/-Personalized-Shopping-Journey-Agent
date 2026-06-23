import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'
import { authChangePassword, authEnable2FA, authDisable2FA, authGetHistory, authGetSessions, authRevokeSession, authVerifyEmail } from '../services/api'
import type { LoginHistoryEntry, UserSession } from '../types'

type Tab = 'security' | 'sessions' | 'history'

export default function Account() {
  const { user, logout } = useAuth()
  const [tab, setTab] = useState<Tab>('security')

  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [pwMsg, setPwMsg] = useState<string | null>(null)
  const [pwLoading, setPwLoading] = useState(false)

  const [twofaMsg, setTwofaMsg] = useState<string | null>(null)
  const [twofaLoading, setTwofaLoading] = useState(false)
  const [twofaSecret, setTwofaSecret] = useState<string | null>(null)

  const [sessions, setSessions] = useState<UserSession[]>([])
  const [sessionsLoading, setSessionsLoading] = useState(false)

  const [history, setHistory] = useState<LoginHistoryEntry[]>([])
  const [historyLoading, setHistoryLoading] = useState(false)

  const loadSessions = async () => {
    setSessionsLoading(true)
    try {
      const res = await authGetSessions()
      setSessions(res.sessions)
    } catch { /* ignore */ }
    setSessionsLoading(false)
  }

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const res = await authGetHistory()
      setHistory(res.entries)
    } catch { /* ignore */ }
    setHistoryLoading(false)
  }

  useEffect(() => {
    if (tab === 'sessions') loadSessions()
    if (tab === 'history') loadHistory()
  }, [tab])

  const handleChangePassword = async () => {
    if (!currentPw || !newPw) { setPwMsg('Fill in both fields'); return }
    setPwLoading(true); setPwMsg(null)
    try {
      const res = await authChangePassword(currentPw, newPw)
      setPwMsg(res.message)
      setCurrentPw(''); setNewPw('')
    } catch (err: unknown) {
      setPwMsg((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed')
    }
    setPwLoading(false)
  }

  const handleToggle2FA = async () => {
    setTwofaLoading(true); setTwofaMsg(null)
    try {
      if (user?.twofa_enabled) {
        await authDisable2FA()
        setTwofaMsg('2FA disabled')
        setTwofaSecret(null)
      } else {
        const res = await authEnable2FA()
        setTwofaMsg('2FA enabled')
        setTwofaSecret(res.demo_code)
      }
    } catch (err: unknown) {
      setTwofaMsg((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed')
    }
    setTwofaLoading(false)
  }

  const handleVerifyEmail = async () => {
    try {
      await authVerifyEmail()
    } catch { /* ignore */ }
  }

  const handleRevokeSession = async (id: string) => {
    try {
      await authRevokeSession(id)
      loadSessions()
    } catch { /* ignore */ }
  }

  if (!user) return null

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="page-title">
            Account
          </motion.h1>
          <p className="page-subtitle">Manage your security & sessions</p>
        </div>
        <button className="btn btn-danger" onClick={logout} style={{ height: 36 }}>
          Sign Out
        </button>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div className="logo-icon-glow" style={{ width: 48, height: 48 }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{user.username}</h2>
            <p style={{ margin: '0.15rem 0', fontSize: '0.85rem', color: 'var(--text-dim)' }}>
              {user.email} {user.email_verified ? '✓ Verified' : '✗ Unverified'}
              {!user.email_verified && (
                <button className="btn" onClick={handleVerifyEmail}
                  style={{ marginLeft: '0.5rem', fontSize: '0.75rem', height: 24, padding: '0 8px' }}>
                  Verify
                </button>
              )}
            </p>
            <span className={`tag`} style={{
              background: user.role === 'admin' ? 'rgba(239,68,68,0.15)' : user.role === 'premium' ? 'rgba(245,158,11,0.15)' : 'rgba(99,102,241,0.15)',
              color: user.role === 'admin' ? '#ef4444' : user.role === 'premium' ? '#f59e0b' : '#818cf8',
              fontSize: '0.75rem',
            }}>
              {user.role}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {(['security', 'sessions', 'history'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`btn ${tab === t ? 'btn-primary' : ''}`}
            style={{ fontSize: '0.85rem', textTransform: 'capitalize' }}>
            {t === 'security' && '🔒 '}{t === 'sessions' && '🖥 '}{t === 'history' && '📋 '}
            {t}
          </button>
        ))}
      </div>

      {tab === 'security' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="card" style={{ marginBottom: '1rem' }}>
            <p className="section-title" style={{ marginBottom: '0.75rem' }}>Change Password</p>
            <div className="form-row">
              <div className="form-group" style={{ flex: 1 }}>
                <label>Current Password</label>
                <input className="input" type="password" value={currentPw} onChange={e => setCurrentPw(e.target.value)} />
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>New Password</label>
                <input className="input" type="password" value={newPw} onChange={e => setNewPw(e.target.value)} />
              </div>
            </div>
            {pwMsg && <div className={`alert alert-${pwMsg.includes('success') ? 'success' : 'error'}`} style={{ marginBottom: '0.5rem' }}>{pwMsg}</div>}
            <button className="btn btn-primary" onClick={handleChangePassword} disabled={pwLoading}>
              {pwLoading ? 'Updating...' : 'Update Password'}
            </button>
          </div>

          <div className="card" style={{ marginBottom: '1rem' }}>
            <p className="section-title" style={{ marginBottom: '0.75rem' }}>
              Two-Factor Authentication {user.twofa_enabled ? <span className="tag" style={{ background: '#1a3a2a', color: '#2bd47c' }}>Enabled</span> : <span className="tag" style={{ background: '#3a1a2a', color: '#ef5566' }}>Disabled</span>}
            </p>
            {twofaSecret && (
              <div style={{ padding: '0.75rem', background: 'rgba(43,212,124,0.1)', borderRadius: 8, marginBottom: '0.75rem', fontSize: '0.85rem' }}>
                <strong>Demo code:</strong> <code style={{ fontSize: '1.2rem', letterSpacing: '0.2em' }}>{twofaSecret}</code>
                <p style={{ color: 'var(--text-dim)', marginTop: '0.25rem', fontSize: '0.75rem' }}>
                  In production this would be in your authenticator app.
                </p>
              </div>
            )}
            {twofaMsg && !twofaSecret && <div className={`alert alert-${twofaMsg.includes('enabled') ? 'success' : twofaMsg.includes('disabled') ? 'info' : 'error'}`} style={{ marginBottom: '0.5rem' }}>{twofaMsg}</div>}
            <button className={`btn ${user.twofa_enabled ? 'btn-danger' : 'btn-primary'}`} onClick={handleToggle2FA} disabled={twofaLoading}>
              {twofaLoading ? 'Processing...' : user.twofa_enabled ? 'Disable 2FA' : 'Enable 2FA'}
            </button>
          </div>
        </motion.div>
      )}

      {tab === 'sessions' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <p className="section-title" style={{ margin: 0 }}>Active Sessions</p>
              <button className="btn" onClick={loadSessions} disabled={sessionsLoading} style={{ height: 30, fontSize: '0.8rem' }}>
                {sessionsLoading ? 'Loading...' : '↻ Refresh'}
              </button>
            </div>
            {sessions.length === 0 ? (
              <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>No active sessions.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {sessions.map(s => (
                  <div key={s.id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.75rem', background: 'var(--surface2)', borderRadius: 8,
                  }}>
                    <div style={{ fontSize: '0.85rem' }}>
                      <div style={{ fontWeight: 600 }}>{s.device_info || 'Unknown device'}</div>
                      <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                        IP: {s.ip_address} · Last active: {new Date(s.last_activity).toLocaleString()}
                      </div>
                    </div>
                    <button className="btn btn-danger" onClick={() => handleRevokeSession(s.id)}
                      style={{ height: 28, fontSize: '0.75rem', padding: '0 10px' }}>
                      Revoke
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {tab === 'history' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <p className="section-title" style={{ margin: 0 }}>Login History</p>
              <button className="btn" onClick={loadHistory} disabled={historyLoading} style={{ height: 30, fontSize: '0.8rem' }}>
                {historyLoading ? 'Loading...' : '↻ Refresh'}
              </button>
            </div>
            {history.length === 0 ? (
              <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>No login history yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {history.map(h => (
                  <div key={h.id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.6rem 0.75rem', background: 'var(--surface2)', borderRadius: 8, fontSize: '0.85rem',
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{
                          width: 8, height: 8, borderRadius: '50%',
                          background: h.success ? '#2bd47c' : '#ef5566',
                          display: 'inline-block',
                        }} />
                        <span>{h.success ? 'Successful' : 'Failed'}</span>
                        {h.fail_reason && <span style={{ color: 'var(--text-dim)' }}>— {h.fail_reason}</span>}
                      </div>
                      <div style={{ color: 'var(--text-dim)', fontSize: '0.75rem', marginTop: '0.15rem' }}>
                        {h.device_info || 'Unknown'} · {h.ip_address}
                      </div>
                    </div>
                    <span style={{ color: 'var(--text-dim)', fontSize: '0.75rem', flexShrink: 0 }}>
                      {new Date(h.timestamp).toLocaleString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  )
}
