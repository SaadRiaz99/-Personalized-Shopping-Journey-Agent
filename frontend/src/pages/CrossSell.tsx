import { useState } from 'react'
import { motion } from 'framer-motion'
import { getCrossSell, addToWishlist } from '../services/api'
import type { CrossSellResult, CrossSellItem } from '../types'
import { catalogSearch } from '../services/api'

const TYPE_COLORS: Record<string, string> = {
  complementary: '#818cf8',
  upsell: '#f59e0b',
  accessory: '#2bd47c',
}

const TYPE_ICONS: Record<string, string> = {
  complementary: '↔',
  upsell: '↑',
  accessory: '◇',
}

export default function CrossSell() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Record<string, unknown>[]>([])
  const [selectedProduct, setSelectedProduct] = useState<Record<string, unknown> | null>(null)
  const [result, setResult] = useState<CrossSellResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearchLoading(true)
    try {
      const res = await catalogSearch({ query: searchQuery, page_size: 8 })
      setSearchResults(res.products as unknown as Record<string, unknown>[])
    } catch { setSearchResults([]) }
    setSearchLoading(false)
  }

  const handleSelectProduct = async (product: Record<string, unknown>) => {
    setSelectedProduct(product)
    setLoading(true)
    setResult(null)
    try {
      const res = await getCrossSell(product.id as number)
      setResult(res)
    } catch { setResult(null) }
    setLoading(false)
  }

  const handleSave = async (item: CrossSellItem) => {
    const p = item.product as Record<string, unknown>
    try {
      await addToWishlist({
        product_id: p.id as number,
        product_name: p.name as string,
        product_price: p.price as number,
        product_category: p.category as string,
        product_image: (p.image_url as string) || null,
        note: `Cross-sell: ${item.type} for ${selectedProduct?.name as string}`,
      })
    } catch { /* ignore */ }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="page-title">
            Cross-sell & Upsell
          </motion.h1>
          <p className="page-subtitle">Discover complementary products and premium upgrades</p>
        </div>
      </div>

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <p className="section-title" style={{ marginBottom: '0.75rem' }}>Find Products to Cross-sell</p>
        <div className="form-row">
          <div className="form-group" style={{ flex: 1 }}>
            <label>Search Products</label>
            <input className="input" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="e.g. headphones, shoes, camera..." />
          </div>
          <button className="btn btn-primary" onClick={handleSearch} disabled={searchLoading}
            style={{ height: 36, marginTop: 22 }}>
            {searchLoading ? 'Searching...' : '🔍 Search'}
          </button>
        </div>

        {searchResults.length > 0 && (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
            {searchResults.map(p => (
              <button key={p.id as number} onClick={() => handleSelectProduct(p)}
                className={`btn ${selectedProduct?.id === p.id ? 'btn-primary' : ''}`}
                style={{ fontSize: '0.8rem', padding: '6px 12px' }}>
                {p.name as string} — ${(p.price as number).toFixed(2)}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <p style={{ color: 'var(--text-dim)' }}>Analyzing product for cross-sell opportunities...</p>
        </div>
      )}

      {result && !loading && (
        <>
          <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '4px solid var(--primary)' }}>
            <p className="section-title" style={{ marginBottom: '0.25rem' }}>Cross-sell Agent Report</p>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-dim)' }}>
              Based on <strong>{result.source_product.name as string}</strong> (${(result.source_product.price as number).toFixed(2)})
              — found {result.recommendations.length} recommendations
            </p>
          </div>

          {result.recommendations.length === 0 ? (
            <div className="empty-state" style={{ padding: '3rem' }}>
              <p>No cross-sell recommendations found for this product. Try a different product.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {(['complementary', 'accessory', 'upsell'] as const).map(type => {
                const items = result.recommendations.filter(r => r.type === type)
                if (items.length === 0) return null
                return (
                  <div key={type}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <span className="status-pill" style={{
                        background: `${TYPE_COLORS[type]}15`,
                        color: TYPE_COLORS[type],
                      }}>
                        {TYPE_ICONS[type]} {type.charAt(0).toUpperCase() + type.slice(1)} ({items.length})
                      </span>
                    </div>
                    {items.map((item, i) => {
                      const p = item.product as Record<string, unknown>
                      return (
                        <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                          className="card animate-in" style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            marginBottom: '0.4rem', borderLeft: `3px solid ${TYPE_COLORS[type]}`,
                          }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <strong style={{ fontSize: '0.95rem' }}>{p.name as string}</strong>
                              <span className="tag" style={{ background: '#2d3748', color: type === 'upsell' ? '#f59e0b' : 'var(--text)', fontSize: '0.7rem' }}>
                                ${(p.price as number).toFixed(2)}
                              </span>
                              <span className="tag" style={{ background: '#2d3748', color: '#a0aec0', fontSize: '0.7rem' }}>
                                {p.category as string}
                              </span>
                            </div>
                            <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', margin: '0.15rem 0' }}>
                              {item.reason}
                            </p>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                              {(item.match_score * 100).toFixed(0)}%
                            </span>
                            <button className="btn" onClick={() => handleSave(item)}
                              style={{ height: 28, fontSize: '0.75rem', padding: '0 10px' }}>
                              ♡ Save
                            </button>
                          </div>
                        </motion.div>
                      )
                    })}
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {!selectedProduct && !loading && (
        <div className="empty-state" style={{ padding: '4rem 2rem' }}>
          <div className="logo-icon-glow" style={{ width: '64px', height: '64px', margin: '0 auto 1.5rem', opacity: 0.4 }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h3 style={{ color: 'var(--text-muted)' }}>No product selected</h3>
          <p style={{ maxWidth: '400px', margin: '0.75rem auto', color: 'var(--text-dim)', fontSize: '0.9rem' }}>
            Search for a product above to see complementary items, accessories, and premium upgrades.
          </p>
        </div>
      )}
    </div>
  )
}
