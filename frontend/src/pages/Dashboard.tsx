import { useEffect, useState } from 'react'
import { getAgents, getProducts } from '../services/api'
import type { Agent, Product } from '../types'

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [products, setProducts] = useState<Product[]>([])

  useEffect(() => {
    getAgents().then(setAgents)
    getProducts({ max_price: 100 }).then(setProducts)
  }, [])

  const running = agents.filter(a => a.status === 'running').length
  const completed = agents.filter(a => a.status === 'completed').length

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Overview of your shopping agents and products</p>
        </div>
      </div>

      <div className="stats">
        <div className="stat-card animate-in">
          <div className="stat-icon">◆</div>
          <strong>{agents.length}</strong>
          <span className="stat-label">Total Agents</span>
        </div>
        <div className="stat-card animate-in">
          <div className="stat-icon">▶</div>
          <strong>{running}</strong>
          <span className="stat-label">Running</span>
        </div>
        <div className="stat-card animate-in">
          <div className="stat-icon">✓</div>
          <strong>{completed}</strong>
          <span className="stat-label">Completed</span>
        </div>
        <div className="stat-card animate-in">
          <div className="stat-icon">✦</div>
          <strong>{products.length}</strong>
          <span className="stat-label">Products Found</span>
        </div>
      </div>

      <h3>Recent Agents</h3>
      <div className="grid">
        {agents.slice(-4).reverse().map(a => (
          <div key={a.id} className="card animate-in">
            <div className="card-header">
              <h4>{a.name}</h4>
              <span className={`status status-${a.status}`}>
                <span className="status-dot" />
                {a.status}
              </span>
            </div>
          </div>
        ))}
        {agents.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">◆</div>
            <p>No agents yet. Create one from the Agents page.</p>
          </div>
        )}
      </div>
    </div>
  )
}
