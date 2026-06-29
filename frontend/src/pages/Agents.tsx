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
    getAgents()
      .then(setAgents)
      .catch(() => setError('Failed to refresh agents'))
  }

  const handleCreate = async () => {
    if (!name.trim()) return
    setError(null)
    try {
      await createAgent(name.trim(), task.trim() || undefined)
      setName('')
      setTask('')
      setPreview(null)
      load()
    } catch { setError('Failed to create agent') }
  }

  const handleRun = async (id: string) => {
    setError(null)
    try {
      await runAgent(id)
      load()
    } catch { setError('Failed to run agent') }
  }

  const handleDelete = async (id: string) => {
    setError(null)
    try {
      await deleteAgent(id)
      load()
    } catch { setError('Failed to delete agent') }
  }

  const handlePreview = async () => {
    if (!task.trim()) return
    setPreviewLoading(true)
    setError(null)
    try {
      const intent = await decodeIntent(task.trim())
      setPreview(intent)
    } catch {
      setError('Failed to parse intent')
      setPreview(null)
    }
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
            <input
              id="agent-name"
              className="input"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Weekend Deals Scout"
              aria-label="Agent name"
            />
          </div>
          <div className="form-group" style={{ flex: 2, minWidth: 240 }}>
            <label htmlFor="agent-task">Task (optional)</label>
            <input
              id="agent-task"
              className="input"
              value={task}
              onChange={e => {
                setTask(e.target.value)
                setPreview(null)
              }}
              placeholder='e.g. Find best deals under $50'
              aria-label="Agent task description"
            />
          </div>
          <button className="btn btn-primary" onClick={handleCreate} style={{ height: 36 }} aria-label="Create agent">
            + Create
          </button>
        </div>
        {task.trim() && (
          <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <button className="btn" onClick={handlePreview} disabled={previewLoading} style={{ height: 32, fontSize: '0.8rem' }} aria-label="Preview parsed intent">
              {previewLoading ? 'Parsing...' : 'Preview Intent'}
            </button>
            {preview && (
              <span style={{ fontSize: '0.85rem', color: '#a0aec0' }} role="status" aria-label="Intent preview">
                {[
                  preview.category && `Category: ${preview.category}`,
                  preview.budget && `Budget: $${preview.budget}`,
                  preview.occasion && `Occasion: ${preview.occasion}`,
                  preview.urgency && `Urgency: ${preview.urgency}`,
                  preview.style_preferences?.length ? `Style: ${preview.style_preferences.join(', ')}` : null,
                ].filter(Boolean).join(' · ')}
              </span>
            )}
          </div>
        )}
      </div>

      <div className="section-header" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Active Agents</h2>
        <span className="page-subtitle">{agents.length} Agents configured</span>
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }} role="status">
          <p style={{ color: 'var(--text-dim)' }}>Loading agents...</p>
        </div>
      ) : (
        <div className="agent-list-container">
          {agents.map(a => (
            <div key={a.id} className="agent-row animate-in">
              <div className="agent-info">
                <div className="agent-name">{a.name}</div>
                <div className="agent-task">{a.task || 'No task assigned'}</div>
              </div>
              <div className="agent-meta">
                <div className={`status status-${a.status}`}>
                  <span className="status-dot"></span>
                  {a.status}
                </div>
                <div className="card-actions" style={{ padding: 0, marginTop: 0 }}>
                  <button 
                    className="btn btn-primary" 
                    onClick={() => handleRun(a.id)}
                    disabled={a.status === 'running'}
                    aria-label={`Run agent ${a.name}`}
                  >
                    {a.status === 'running' ? 'Running...' : 'Run'}
                  </button>
                  <button className="btn btn-danger" onClick={() => handleDelete(a.id)} aria-label={`Delete agent ${a.name}`}>
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      {!loading && agents.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon" aria-hidden="true">◆</div>
          <p>No agents yet. Create one above to get started.</p>
        </div>
      )}
    </div>
  )
}
