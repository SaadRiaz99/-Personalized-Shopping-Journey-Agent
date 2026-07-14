import { useState } from 'react'
import { motion } from 'framer-motion'
import { getCrossSell, addToWishlist, catalogSearch } from '../services/api'
import type { CrossSellResult, CrossSellItem, CatalogProduct } from '../types'

const TYPE_COLORS: Record<string, string> = { complementary: 'var(--primary)', upsell: 'var(--warning)', accessory: 'var(--success)' }
const TYPE_ICONS: Record<string, string> = { complementary: '\u2194', upsell: '\u2191', accessory: '\u25C7' }

export default function CrossSell() {
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<CatalogProduct[]>([])
  const [selectedProduct, setSelectedProduct] = useState<CatalogProduct | null>(null)
  const [result, setResult] = useState<CrossSellResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [searchLoading, setSearchLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearchLoading(true); setError(null)
    try { const res = await catalogSearch({ query: searchQuery, page_size: 8 }); setSearchResults(res.products) }
    catch { setError('Search failed.'); setSearchResults([]) }
    setSearchLoading(false)
  }

  const handleSelectProduct = async (product: CatalogProduct) => {
    setSelectedProduct(product); setLoading(true); setResult(null); setError(null)
    try { setResult(await getCrossSell(product.id)) }
    catch { setError('Failed to load cross-sell recommendations.'); setResult(null) }
    setLoading(false)
  }

  const handleSave = async (item: CrossSellItem) => {
    const p = item.product
    try {
      await addToWishlist({
        product_id: p.id as number, product_name: p.name as string, product_price: p.price as number,
        product_category: p.category as string, product_image: (p.image_url as string) || null,
        note: `Cross-sell: ${item.type} for ${selectedProduct?.name as string}`,
      })
    } catch { setError('Failed to save to wishlist.') }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="page-title">Cross-sell & Upsell</motion.h1>
          <p className="page-subtitle">Discover complementary products and premium upgrades</p>
        </div>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <p className="section-title" style={{ marginBottom: '0.75rem' }}>Find Products to Cross-sell</p>
        <div className="form-row">
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="crossell-search">Search Products</label>
            <input id="crossell-search" className="input" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="e.g. headphones, shoes, camera..." />
          </div>
          <button className="btn btn-primary" onClick={handleSearch} disabled={searchLoading}
            style={{ height: 38, marginTop: 22 }}>
            {searchLoading ? <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span className="spinner" /> Searching...</span> : 'Search'}
          </button>
        </div>
        {searchResults.length > 0 && (
          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap', marginTop: '0.75rem' }} role="list">
            {searchResults.map(p => (
              <button key={p.id} onClick={() => handleSelectProduct(p)}
                className={`btn ${selectedProduct?.id === p.id ? 'btn-primary' : 'btn-ghost'}`}
                style={{ fontSize: '0.78rem', padding: '6px 12px' }}>
                {p.name} {"\u2014"} ${p.price.toFixed(2)}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }} role="status">
          <span className="spinner" style={{ margin: '0 auto', display: 'block' }} />
          <p style={{ color: 'var(--text-dim)', marginTop: '0.75rem' }}>Analyzing product for cross-sell opportunities...</p>
        </div>
      )}

      {result && !loading && (
        <>
          <div className="card" style={{ marginBottom: '1.5rem', borderLeft: '3px solid var(--primary)' }}>
            <p className="section-title" style={{ marginBottom: '0.25rem' }}>Cross-sell Agent Report</p>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Based on <strong style={{ color: 'var(--text)' }}>{result.source_product.name as string}</strong> (${(result.source_product.price as number).toFixed(2)})
              {"\u2014"} found {result.recommendations.length} recommendations
            </p>
          </div>

          {result.recommendations.length === 0 ? (
            <div className="empty-state" style={{ padding: '3rem' }}>
              <p>No cross-sell recommendations found. Try a different product.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {(['complementary', 'accessory', 'upsell'] as const).map(type => {
                const items = result.recommendations.filter(r => r.type === type)
                if (items.length === 0) return null
                return (
                  <div key={type}>
                    <span className="status-pill" style={{
                      background: `${TYPE_COLORS[type]}12`, color: TYPE_COLORS[type],
                      border: `1px solid ${TYPE_COLORS[type]}25`, marginBottom: '0.5rem',
                    }}>
                      {TYPE_ICONS[type]} {type.charAt(0).toUpperCase() + type.slice(1)} ({items.length})
                    </span>
                    {items.map((item, i) => {
                      const p = item.product
                      return (
                        <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                          className="card animate-in" style={{
                            flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
                            marginTop: '0.4rem', borderLeft: `3px solid ${TYPE_COLORS[type]}`,
                            padding: '0.85rem 1rem',
                          }}>
                          <div style={{ flex: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                              <strong style={{ fontSize: '0.9rem' }}>{p.name as string}</strong>
                              <span className="tag" style={{ background: 'var(--primary-glow)', color: 'var(--primary)' }}>${(p.price as number).toFixed(2)}</span>
                              <span className="tag">{p.category as string}</span>
                            </div>
                            <p style={{ fontSize: '0.78rem', color: 'var(--text-dim)', margin: '0.25rem 0 0' }}>{item.reason}</p>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexShrink: 0 }}>
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>{(item.match_score * 100).toFixed(0)}%</span>
                            <button className="btn btn-ghost" onClick={() => handleSave(item)} style={{ height: 28, fontSize: '0.72rem', padding: '0 10px' }}>Save</button>
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
          <div className="logo-icon-glow" style={{ width: 60, height: 60, margin: '0 auto 1.25rem', opacity: 0.4 }} aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h3 style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>No product selected</h3>
          <p style={{ maxWidth: 380, margin: '0.75rem auto', color: 'var(--text-dim)', fontSize: '0.9rem' }}>
            Search for a product above to see complementary items, accessories, and premium upgrades.
          </p>
        </div>
      )}
    </div>
  )
}
