import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { getAdminStats, getAdminUsers, updateAdminUser } from '../services/api'
import type { AdminStats, AuthUser } from '../types'

export default function Admin() {
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [users, setUsers] = useState<AuthUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getAdminStats(), getAdminUsers()])
      .then(([s, u]) => {
        setStats(s)
        setUsers(u.users)
      })
      .catch(() => setError('Failed to load admin data'))
      .finally(() => setLoading(false))
  }, [])

  const toggleUserStatus = async (user: AuthUser) => {
    try {
      await updateAdminUser(user.id, { disabled: !user.twofa_enabled })
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, twofa_enabled: !u.twofa_enabled } : u))
    } catch {
      setError('Failed to update user')
    }
  }

  if (loading) return <div className="loading-state">Loading admin dashboard...</div>

  return (
    <div className="admin-page">
      <h2>Admin Dashboard</h2>

      {error && <div className="error-msg">{error}</div>}

      {stats && (
        <motion.div className="stats-grid" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <div className="stat-card">
            <div className="stat-value">{stats.total_users}</div>
            <div className="stat-label">Users</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.total_documents}</div>
            <div className="stat-label">Documents</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.total_conversations}</div>
            <div className="stat-label">Conversations</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.total_messages}</div>
            <div className="stat-label">Messages</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.storage_used_mb.toFixed(1)} MB</div>
            <div className="stat-label">Storage</div>
          </div>
        </motion.div>
      )}

      <h3 style={{ marginTop: 32, marginBottom: 16 }}>Users</h3>
      <div className="users-table">
        <div className="table-header">
          <span>Username</span>
          <span>Email</span>
          <span>Role</span>
          <span>Status</span>
        </div>
        {users.map(user => (
          <div key={user.id} className="table-row">
            <span>{user.username}</span>
            <span>{user.email}</span>
            <span>
              <span className={`role-badge ${user.role}`}>{user.role}</span>
            </span>
            <span>
              <span className={`status-dot ${user.twofa_enabled ? 'active' : 'inactive'}`} />
              {user.twofa_enabled ? 'Active' : 'Inactive'}
            </span>
          </div>
        ))}
      </div>

      <style>{`
        .admin-page { max-width: 1000px; margin: 0 auto; }
        .admin-page h2 { margin-bottom: 24px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; }
        .stat-card {
          padding: 24px;
          border-radius: 16px;
          background: var(--glass-card);
          border: 1px solid var(--glass-border);
          text-align: center;
        }
        .stat-value { font-size: 2rem; font-weight: 700; color: var(--primary); }
        .stat-label { font-size: 0.85rem; color: var(--text-dim); margin-top: 4px; }
        .users-table { border-radius: 12px; overflow: hidden; border: 1px solid var(--glass-border); }
        .table-header, .table-row { display: grid; grid-template-columns: 2fr 2fr 1fr 1fr; padding: 12px 16px; gap: 8px; align-items: center; }
        .table-header { background: var(--glass-highlight); font-weight: 600; font-size: 0.85rem; color: var(--text-dim); }
        .table-row { border-top: 1px solid var(--glass-border); font-size: 0.9rem; transition: var(--transition-smooth); }
        .table-row:hover { background: var(--glass-highlight); }
        .role-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: 600; }
        .role-badge.admin { background: rgba(99,102,241,0.2); color: #818cf8; }
        .role-badge.user { background: rgba(52,211,153,0.2); color: #34d399; }
        .status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
        .status-dot.active { background: var(--success); }
        .status-dot.inactive { background: var(--text-dim); }
        .loading-state { text-align: center; padding: 60px 20px; color: var(--text-dim); }
        .error-msg { color: var(--danger); font-size: 0.85rem; padding: 8px 12px; border-radius: 8px; background: rgba(255,0,0,0.1); margin-bottom: 12px; }
      `}</style>
    </div>
  )
}
