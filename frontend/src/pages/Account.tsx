import { useState, useEffect, useRef } from 'react'
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
  const [error, setError] = useState<string | null>(null)
  const isMounted = useRef(true)

  useEffect(() => { isMounted.current = true; return () => { isMounted.current = false } }, [])

  const loadSessions = async () => {
    setSessionsLoading(true); setError(null)
    try { const res = await authGetSessions(); if (isMounted.current) setSessions(res.sessions) }
    catch { if (isMounted.current) setError('Failed to load sessions') }
    if (isMounted.current) setSessionsLoading(false)
  }

  const loadHistory = async () => {
    setHistoryLoading(true); setError(null)
    try { const res = await authGetHistory(); if (isMounted.current) setHistory(res.entries) }
    catch { if (isMounted.current) setError('Failed to load login history') }
    if (isMounted.current) setHistoryLoading(false)
  }

  useEffect(() => {
    const load = async () => { if (tab === 'sessions') await loadSessions(); if (tab === 'history') await loadHistory() }
    load()
  }, [tab])

  const handleChangePassword = async () => {
    if (!currentPw || !newPw) { setPwMsg('Fill in both fields'); return }
    setPwLoading(true); setPwMsg(null)
    try { const res = await authChangePassword(currentPw, newPw); setPwMsg(res.message); setCurrentPw(''); setNewPw('') }
    catch (err: unknown) { setPwMsg((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed') }
    setPwLoading(false)
  }

  const handleToggle2FA = async () => {
    setTwofaLoading(true); setTwofaMsg(null)
    try {
      if (user?.twofa_enabled) { await authDisable2FA(); setTwofaMsg('2FA disabled'); setTwofaSecret(null) }
      else { const res = await authEnable2FA(); setTwofaMsg(res.message); setTwofaSecret(res.secret) }
    } catch (err: unknown) { setTwofaMsg((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed') }
    setTwofaLoading(false)
  }

  const handleVerifyEmail = async () => {
    try { await authVerifyEmail() } catch { setError('Failed to send verification email') }
  }

  const handleRevokeSession = async (id: string) => {
    try { await authRevokeSession(id); loadSessions() } catch { setError('Failed to revoke session') }
  }

  if (!user) return null

  const TAB_CONFIG = [
    { key: 'security' as Tab, label: 'Security', icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg> },
    { key: 'sessions' as Tab, label: 'Sessions', icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg> },
    { key: 'history' as Tab, label: 'History', icon: <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg> },
  ]

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="page-title">Account</motion.h1>
          <p className="page-subtitle">Manage your security & sessions</p>
        </div>
        <button className="btn btn-danger" onClick={logout} style={{ height: 38 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          Sign Out
        </button>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: 48, height: 48, borderRadius: 'var(--radius-md)',
            background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(129,140,248,0.2)',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.1rem' }}>{user.username}</h2>
            <p style={{ margin: '0.15rem 0', fontSize: '0.82rem', color: 'var(--text-dim)' }}>
              {user.email} {user.email_verified ? '\u2713 Verified' : '\u2717 Unverified'}
              {!user.email_verified && (
                <button className="btn btn-ghost" onClick={handleVerifyEmail}
                  style={{ marginLeft: '0.5rem', fontSize: '0.72rem', height: 24, padding: '0 8px' }}>Verify</button>
              )}
            </p>
            <span className="tag" style={{
              background: user.role === 'admin' ? 'var(--danger-glow)' : 'var(--primary-glow)',
              color: user.role === 'admin' ? 'var(--danger)' : 'var(--primary)',
              border: `1px solid ${user.role === 'admin' ? 'rgba(244,63,94,0.15)' : 'rgba(129,140,248,0.15)'}`,
            }}>
              {user.role}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '1.5rem' }}>
        {TAB_CONFIG.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`btn ${tab === t.key ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: '0.82rem', display: 'flex', alignItems: 'center', gap: 6 }}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {tab === 'security' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
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
            {pwMsg && <div className={pwMsg.includes('success') ? 'alert alert-success' : 'alert alert-error'} style={{ marginTop: '0.5rem' }}>{pwMsg}</div>}
            <button className="btn btn-primary" onClick={handleChangePassword} disabled={pwLoading}
              style={{ marginTop: '0.75rem' }}>
              {pwLoading ? <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span className="spinner" /> Updating...</span> : 'Update Password'}
            </button>
          </div>

          <div className="card">
            <p className="section-title" style={{ marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              Two-Factor Authentication
              <span className="tag" style={{
                background: user.twofa_enabled ? 'var(--success-glow)' : 'var(--danger-glow)',
                color: user.twofa_enabled ? 'var(--success)' : 'var(--danger)',
                border: `1px solid ${user.twofa_enabled ? 'rgba(16,185,129,0.15)' : 'rgba(244,63,94,0.15)'}`,
              }}>
                {user.twofa_enabled ? 'Enabled' : 'Disabled'}
              </span>
            </p>
            {twofaSecret && (
              <div style={{ padding: '1rem', background: 'var(--success-glow)', borderRadius: 'var(--radius-sm)', marginBottom: '0.75rem', border: '1px solid rgba(16,185,129,0.15)' }}>
                <strong style={{ fontSize: '0.82rem' }}>Authenticator setup key:</strong> <code style={{ fontSize: '0.9rem', color: 'var(--success)', wordBreak: 'break-all' }}>{twofaSecret}</code>
                <p style={{ color: 'var(--text-dim)', marginTop: '0.25rem', fontSize: '0.72rem' }}>Add this key to Google Authenticator, Authy, or another TOTP app. It will only be shown now.</p>
              </div>
            )}
            {twofaMsg && !twofaSecret && <div className={twofaMsg.includes('enabled') ? 'alert alert-success' : 'alert alert-info'} style={{ marginBottom: '0.5rem' }}>{twofaMsg}</div>}
            <button className={`btn ${user.twofa_enabled ? 'btn-danger' : 'btn-primary'}`} onClick={handleToggle2FA} disabled={twofaLoading}>
              {twofaLoading ? <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span className="spinner" /> Processing...</span> : user.twofa_enabled ? 'Disable 2FA' : 'Enable 2FA'}
            </button>
          </div>
        </motion.div>
      )}

      {tab === 'sessions' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <p className="section-title" style={{ margin: 0 }}>Active Sessions</p>
              <button className="btn btn-ghost" onClick={loadSessions} disabled={sessionsLoading} style={{ height: 30, fontSize: '0.78rem' }}>
                {sessionsLoading ? <span className="spinner" /> : '\u21BB Refresh'}
              </button>
            </div>
            {sessions.length === 0 ? (
              <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem' }}>No active sessions.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {sessions.map(s => (
                  <div key={s.id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.75rem 1rem', background: 'var(--glass)', borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--glass-border)',
                  }}>
                    <div style={{ fontSize: '0.82rem' }}>
                      <div style={{ fontWeight: 600 }}>{s.device_info || 'Unknown device'}</div>
                      <div style={{ color: 'var(--text-dim)', fontSize: '0.72rem', marginTop: 2 }}>
                        IP: {s.ip_address} {"\u00b7"} Last active: {new Date(s.last_activity).toLocaleString()}
                      </div>
                    </div>
                    <button className="btn btn-danger" onClick={() => handleRevokeSession(s.id)}
                      style={{ height: 28, fontSize: '0.72rem', padding: '0 10px' }}>Revoke</button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </motion.div>
      )}

      {tab === 'history' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <p className="section-title" style={{ margin: 0 }}>Login History</p>
              <button className="btn btn-ghost" onClick={loadHistory} disabled={historyLoading} style={{ height: 30, fontSize: '0.78rem' }}>
                {historyLoading ? <span className="spinner" /> : '\u21BB Refresh'}
              </button>
            </div>
            {history.length === 0 ? (
              <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem' }}>No login history yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {history.map(h => (
                  <div key={h.id} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '0.6rem 0.85rem', background: 'var(--glass)', borderRadius: 'var(--radius-sm)',
                    fontSize: '0.82rem', border: '1px solid var(--glass-border)',
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span style={{ width: 7, height: 7, borderRadius: '50%', background: h.success ? 'var(--success)' : 'var(--danger)' }} />
                        <span>{h.success ? 'Successful' : 'Failed'}</span>
                        {h.fail_reason && <span style={{ color: 'var(--text-dim)' }}>{"\u2014"} {h.fail_reason}</span>}
                      </div>
                      <div style={{ color: 'var(--text-dim)', fontSize: '0.72rem', marginTop: 2 }}>{h.device_info || 'Unknown'} {"\u00b7"} {h.ip_address}</div>
                    </div>
                    <span style={{ color: 'var(--text-dim)', fontSize: '0.72rem', flexShrink: 0 }}>{new Date(h.timestamp).toLocaleString()}</span>
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
