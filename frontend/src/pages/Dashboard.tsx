import { useState } from 'react'
import { runCollaboration } from '../services/api'
import ProductCard from '../components/ProductCard'

export default function Dashboard() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)

  const handleCollaboration = async () => {
    if (!query.trim()) return
    setLoading(true)
    try {
      const data = await runCollaboration(query)
      setResult(data)
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Collaboration Council</h1>
          <p className="page-subtitle">Trigger specialized agents to work together on your task</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '2rem' }}>
        <p className="section-title">Initiate Collaborative Search</p>
        <div className="form-row">
          <input 
            className="input" 
            placeholder="What are you looking for? (e.g. 'find a high-end laptop')" 
            value={query}
            onChange={e => setQuery(e.target.value)}
            style={{ flex: 1 }}
          />
          <button 
            className="btn btn-primary" 
            onClick={handleCollaboration} 
            disabled={loading}
            style={{ height: 40 }}
          >
            {loading ? 'Council is deliberating...' : 'Ask the Council'}
          </button>
        </div>
      </div>

      {result && (
        <div className="animate-in">
          <div className="card" style={{ marginBottom: '1.5rem', background: 'var(--primary-subtle)', borderColor: 'var(--primary)' }}>
            <h3 style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>Council Summary</h3>
            <p className="task-text" style={{ fontSize: '1rem', color: 'var(--text)' }}>{result.summary}</p>
          </div>

          <div className="grid">
            {result.products.map((p: any) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </div>
      )}

      {!result && !loading && (
        <div className="empty-state">
          <div className="empty-icon">◈</div>
          <p>Ask the Council a question to start the collaborative multi-agent workflow.</p>
        </div>
      )}
    </div>
  )
}
