import { useEffect, useState } from 'react'
import { getAgents, createAgent, deleteAgent, runAgent, decodeIntent } from '../services/api'
import type { Agent, QueryIntent } from '../types'

export default function Agents() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [name, setName] = useState('')
  const [task, setTask] = useState('')
  const [preview, setPreview] = useState<QueryIntent | null>(null)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getAgents()
      .then(data => { if (!cancelled) setAgents(data) })
      .catch(() => { if (!cancelled) setError('Failed to load agents') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const load = () => {
    getAgents().then(setAgents).catch(() => setError('Failed to refresh agents'))
  }

  const handleCreate = async () => {
    if (!name.trim()) return
    setError(null)
    try {
      await createAgent(name.trim(), task.trim() || undefined)
      setName(''); setTask(''); setPreview(null)
      load()
    } catch { setError('Failed to create agent') }
  }

  const handleRun = async (id: string) => {
    setError(null)
    try { await runAgent(id); load() }
    catch { setError('Failed to run agent') }
  }

  const handleDelete = async (id: string) => {
    setError(null)
    try { await deleteAgent(id); load() }
    catch { setError('Failed to delete agent') }
  }

  const handlePreview = async () => {
    if (!task.trim()) return
    setPreviewLoading(true); setError(null)
    try { const intent = await decodeIntent(task.trim()); setPreview(intent) }
    catch { setError('Failed to parse intent'); setPreview(null) }
    setPreviewLoading(false)
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Agents</h1>
          <p className="page-subtitle">Create and manage your shopping agents</p>
        </div>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <p className="section-title" style={{ marginBottom: '0.75rem' }}>New Agent</p>
        <div className="form-row">
          <div className="form-group" style={{ flex: 1, minWidth: 180 }}>
            <label htmlFor="agent-name">Name</label>
            <input id="agent-name" className="input" value={name} onChange={e => setName(e.target.value)}
              placeholder="e.g. Weekend Deals Scout" aria-label="Agent name" />
          </div>
          <div className="form-group" style={{ flex: 2, minWidth: 240 }}>
            <label htmlFor="agent-task">Task (optional)</label>
            <input id="agent-task" className="input" value={task} onChange={e => { setTask(e.target.value); setPreview(null) }}
              placeholder="e.g. Find best deals under $50" aria-label="Agent task description" />
          </div>
          <button className="btn btn-primary" onClick={handleCreate} style={{ height: 38 }} aria-label="Create agent">
            + Create
          </button>
        </div>
        {task.trim() && (
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button className="btn btn-ghost" onClick={handlePreview} disabled={previewLoading}
              style={{ height: 32, fontSize: '0.78rem' }} aria-label="Preview parsed intent">
              {previewLoading ? <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span className="spinner" /> Parsing...</span> : 'Preview Intent'}
            </button>
            {preview && (
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }} role="status">
                {[
                  preview.category && `Category: ${preview.category}`,
                  preview.budget && `Budget: $${preview.budget}`,
                  preview.occasion && `Occasion: ${preview.occasion}`,
                  preview.urgency && `Urgency: ${preview.urgency}`,
                  preview.style_preferences?.length ? `Style: ${preview.style_preferences.join(', ')}` : null,
                ].filter(Boolean).join(' \u00b7 ')}
              </span>
            )}
          </div>
        )}
      </div>

      <div style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Active Agents</h2>
        <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{agents.length} configured</span>
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }} role="status">
          <span className="spinner" style={{ margin: '0 auto', display: 'block' }} />
          <p style={{ color: 'var(--text-dim)', marginTop: '0.75rem', fontSize: '0.85rem' }}>Loading agents...</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {agents.map((a, i) => (
            <div key={a.id} className="card animate-in" style={{
              flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
              padding: '1rem 1.25rem',
              animationDelay: `${i * 0.04}s`,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flex: 1 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 'var(--radius-sm)',
                  background: a.status === 'completed' ? 'var(--success-glow)' : a.status === 'running' ? 'var(--primary-glow)' : 'var(--glass)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
                  border: `1px solid ${a.status === 'completed' ? 'rgba(16,185,129,0.15)' : a.status === 'running' ? 'rgba(129,140,248,0.15)' : 'var(--glass-border)'}`,
                }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={a.status === 'completed' ? 'var(--success)' : a.status === 'running' ? 'var(--primary)' : 'var(--text-dim)'} strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/>
                  </svg>
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{a.name}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>{a.task || 'No task assigned'}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <div className={`status status-${a.status}`}>
                  <span className="status-dot" />
                  {a.status}
                </div>
                <button className="btn btn-primary" onClick={() => handleRun(a.id)} disabled={a.status === 'running'}
                  style={{ height: 32, fontSize: '0.78rem', padding: '0 14px' }}>
                  {a.status === 'running' ? <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span className="spinner" /> Running</span> : 'Run'}
                </button>
                <button className="btn btn-danger" onClick={() => handleDelete(a.id)}
                  style={{ height: 32, fontSize: '0.78rem', padding: '0 10px' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      {!loading && agents.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon" aria-hidden="true">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
          </div>
          <p>No agents yet. Create one above to get started.</p>
        </div>
      )}
    </div>
  )
}
