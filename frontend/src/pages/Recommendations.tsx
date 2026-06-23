import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getRecommendations } from '../services/api'
import type { Product } from '../types'
import ProductCard from '../components/ProductCard'

export default function Recommendations() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    getRecommendations()
      .then(setProducts)
      .finally(() => setLoading(false))
  }, [refreshKey])

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="page-title"
          >
            Recommendations
          </motion.h1>
          <p className="page-subtitle">
            Personalized picks based on your shopping preferences
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setRefreshKey(k => k + 1)}
          disabled={loading}
          style={{ height: 36 }}
        >
          {loading ? 'Refreshing...' : '↻ Refresh'}
        </button>
      </div>

      {loading ? (
        <div
          className="grid"
          style={{ gap: '1.5rem' }}
        >
          {[1, 2, 3, 4, 5, 6].map(i => (
            <div
              key={i}
              className="card animate-in"
              style={{
                height: 180,
                background:
                  'linear-gradient(135deg, var(--surface2) 25%, var(--surface) 50%, var(--surface2) 75%)',
                backgroundSize: '200% 100%',
                animation: 'shimmer 2s infinite',
              }}
            />
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="empty-state" style={{ padding: '6rem 2rem' }}>
          <div
            className="logo-icon-glow"
            style={{
              width: '64px',
              height: '64px',
              margin: '0 auto 1.5rem',
              opacity: 0.4,
            }}
          >
            <svg
              width="28"
              height="28"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="2"
            >
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            </svg>
          </div>
          <h3 style={{ color: 'var(--text-muted)' }}>
            No recommendations yet
          </h3>
          <p
            style={{
              maxWidth: '400px',
              margin: '0.75rem auto 1.5rem',
              color: 'var(--text-dim)',
              fontSize: '0.9rem',
              lineHeight: '1.6',
            }}
          >
            Set your preferred categories, price range, and brands in Settings
            to get personalized product recommendations.
          </p>
          <a href="/preferences" className="btn btn-cyber">
            Open Settings
          </a>
        </div>
      ) : (
        <>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              marginBottom: '1.5rem',
            }}
          >
            <span className="status-pill" style={{ background: 'var(--primary-glow)', color: 'var(--primary)' }}>
              {products.length} recommendations
            </span>
          </div>

          <motion.div
            layout
            className="grid"
            style={{ gap: '1.5rem' }}
          >
            {products.map((p, i) => (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <ProductCard product={p} />
              </motion.div>
            ))}
          </motion.div>
        </>
      )}
    </div>
  )
}
