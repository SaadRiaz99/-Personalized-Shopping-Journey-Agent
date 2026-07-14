import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getRecommendations } from '../services/api'
import type { Product } from '../types'
import ProductCard from '../components/ProductCard'

export default function Recommendations() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true); setError(null)
    getRecommendations()
      .then(data => { if (!cancelled) setProducts(data) })
      .catch(() => { if (!cancelled) setError('Failed to load recommendations') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [refreshKey])

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="page-title">
            Recommendations
          </motion.h1>
          <p className="page-subtitle">Personalized picks based on your shopping preferences</p>
        </div>
        <button className="btn btn-primary" onClick={() => setRefreshKey(k => k + 1)} disabled={loading}
          style={{ height: 38 }}>
          {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span className="spinner" /> Refreshing...</span> : '\u21BB Refresh'}
        </button>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {loading ? (
        <div className="grid" style={{ gap: '1rem' }} role="status" aria-label="Loading recommendations">
          {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton-card" aria-hidden="true" />)}
        </div>
      ) : products.length === 0 ? (
        <div className="empty-state" style={{ padding: '5rem 2rem' }}>
          <div className="logo-icon-glow" style={{ width: 60, height: 60, margin: '0 auto 1.25rem', opacity: 0.4 }} aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            </svg>
          </div>
          <h3 style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>No recommendations yet</h3>
          <p style={{ maxWidth: 380, margin: '0.75rem auto 1.5rem', color: 'var(--text-dim)', fontSize: '0.9rem', lineHeight: 1.6 }}>
            Set your preferred categories, price range, and brands in Settings to get personalized recommendations.
          </p>
          <a href="/preferences" className="btn btn-primary" style={{ textDecoration: 'none' }}>Open Settings</a>
        </div>
      ) : (
        <>
          <div style={{ marginBottom: '1.25rem' }}>
            <span className="status-pill" style={{ background: 'var(--primary-glow)', color: 'var(--primary)', border: '1px solid rgba(129,140,248,0.15)' }}>
              {products.length} recommendations
            </span>
          </div>
          <motion.div layout className="grid" style={{ gap: '1rem' }}>
            {products.map((p, i) => (
              <motion.div key={p.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}>
                <ProductCard product={p} />
              </motion.div>
            ))}
          </motion.div>
        </>
      )}
    </div>
  )
}
