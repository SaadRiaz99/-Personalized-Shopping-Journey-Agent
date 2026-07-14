import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getPriceMatchProducts, checkPriceMatch, applyDiscount, getPriceAlerts } from '../services/api'
import type { PriceMatchProduct, DiscountResult, PriceDropAlert } from '../types'

function Sparkline({ data, width = 100, height = 28 }: { data: { price: number }[]; width?: number; height?: number }) {
  if (!data.length) return null
  const prices = data.map(d => d.price)
  const min = Math.min(...prices) * 0.98
  const max = Math.max(...prices) * 1.02
  const range = max - min || 1
  const stepX = width / (prices.length - 1)
  const points = prices.map((p, i) => `${i * stepX},${height - ((p - min) / range) * (height - 4) - 2}`).join(' ')
  const trend = prices[prices.length - 1] >= prices[0]
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
      <polyline points={points} fill="none" stroke={trend ? 'var(--success)' : 'var(--danger)'} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function PriceTag({ price, original }: { price: number; original?: number }) {
  if (original && original > price) {
    const saved = ((original - price) / original * 100).toFixed(1)
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <span style={{ textDecoration: 'line-through', color: 'var(--text-dim)', fontSize: '0.8rem' }}>${original.toFixed(2)}</span>
        <span style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--success)' }}>${price.toFixed(2)}</span>
        <span style={{ background: 'var(--success-glow)', color: 'var(--success)', padding: '2px 6px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 700 }}>-{saved}%</span>
      </span>
    )
  }
  return <span style={{ fontWeight: 800, fontSize: '1.1rem' }}>${price.toFixed(2)}</span>
}

export default function PriceMatch() {
  const [products, setProducts] = useState<PriceMatchProduct[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [checking, setChecking] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, DiscountResult>>({})
  const [applying, setApplying] = useState<string | null>(null)
  const [alerts, setAlerts] = useState<{ product_id: string; product_name: string; alerts: PriceDropAlert[] }[]>([])
  const [showAlerts, setShowAlerts] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const userId = 'web_user_001'

  useEffect(() => {
    let cancelled = false
    getPriceMatchProducts()
      .then(data => { if (!cancelled) setProducts(data) })
      .catch(() => { if (!cancelled) setError('Failed to load price match products') })
      .finally(() => { if (!cancelled) setLoading(false) })
    getPriceAlerts(3).then(data => { if (!cancelled) setAlerts(data) }).catch(() => {})
    return () => { cancelled = true }
  }, [])

  const handleCheck = async (p: PriceMatchProduct) => {
    setChecking(p.id); setError(null)
    try { const res = await checkPriceMatch(p.id, p.sku, p.store_price, userId); if (res.discount) setResults(prev => ({ ...prev, [p.id]: res.discount })) }
    catch { setError('Price check failed.') }
    setChecking(null)
  }

  const handleApply = async (discountId: string, productId: string) => {
    setApplying(discountId); setError(null)
    try { const updated = await applyDiscount(discountId); setResults(prev => ({ ...prev, [productId]: updated })) }
    catch { setError('Failed to apply discount.') }
    setApplying(null)
  }

  const totalSavings = Object.values(results).reduce((s, r) => s + (r.status === 'approved' || r.status === 'applied' ? r.discount_amount : 0), 0)
  const approvedCount = Object.values(results).filter(r => r.status === 'approved' || r.status === 'applied').length

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="page-title">Price Match Agent</motion.h1>
          <p className="page-subtitle">Scan competitor pricing across 5 retailers</p>
        </div>
        {alerts.length > 0 && (
          <button className="btn btn-ghost" onClick={() => setShowAlerts(!showAlerts)} style={{ height: 38, position: 'relative' }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            Alerts
            <span style={{ position: 'absolute', top: -4, right: -4, background: 'var(--danger)', color: '#fff', borderRadius: '50%', width: 18, height: 18, fontSize: '0.65rem', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
              {alerts.length}
            </span>
          </button>
        )}
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <AnimatePresence>
        {showAlerts && alerts.length > 0 && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
            className="card" style={{ marginBottom: '1.5rem', overflow: 'hidden', borderLeft: '3px solid var(--warning)' }}>
            <p className="section-title" style={{ marginBottom: '0.5rem' }}>Price Drop Alerts</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              {alerts.map(a => a.alerts.slice(0, 2).map((alert, i) => (
                <div key={`${a.product_id}-${i}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem' }}>
                  <span style={{ fontWeight: 500 }}>{a.product_name}</span>
                  <span style={{ color: 'var(--success)' }}>${alert.from.toFixed(2)} {"\u2192"} ${alert.to.toFixed(2)} <strong style={{ background: 'var(--success-glow)', padding: '2px 6px', borderRadius: 4 }}>-{alert.drop_pct}%</strong></span>
                </div>
              )))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {approvedCount > 0 && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}
          style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem', marginBottom: '1.5rem' }}>
          {[
            { label: 'Total Savings', value: `$${totalSavings.toFixed(2)}`, color: 'var(--success)', icon: '$' },
            { label: 'Price Matches', value: `${approvedCount}/${Object.keys(results).length}`, color: 'var(--primary)', icon: '\u2713' },
            { label: 'Products Scanned', value: products.length.toString(), color: 'var(--warning)', icon: '\u2315' },
            { label: 'Avg Discount', value: approvedCount > 0 ? `$${(totalSavings / approvedCount).toFixed(2)}` : '$0', color: 'var(--danger)', icon: '\u2193' },
          ].map((s, i) => (
            <div key={i} className="card" style={{ padding: '1rem', borderLeft: `3px solid ${s.color}` }}>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{s.label}</span>
              <strong style={{ fontSize: '1.4rem', color: s.color, letterSpacing: '-0.03em' }}>{s.value}</strong>
            </div>
          ))}
        </motion.div>
      )}

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '0.75rem' }}>
          {[1,2,3,4].map(i => <div key={i} className="skeleton-card" style={{ height: 240 }} />)}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '0.75rem' }}>
          {products.map((p, i) => {
            const result = results[p.id]
            const isSelected = selected === p.id
            return (
              <motion.div key={p.id} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
                className="card animate-in" style={{
                  cursor: 'pointer',
                  borderLeft: result?.status === 'approved' || result?.status === 'applied' ? '3px solid var(--success)' : undefined,
                }}
                onClick={() => setSelected(isSelected ? null : p.id)} layout>
                <div className="card-header">
                  <div>
                    <h3 style={{ fontSize: '0.9rem', margin: 0 }}>{p.name}</h3>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>{p.category}</span>
                  </div>
                  <span style={{ color: 'var(--warning)', fontSize: '0.8rem' }}>
                    <span aria-hidden="true">{'\u2605'.repeat(Math.round(p.rating))}</span>
                    <span style={{ color: 'var(--text-dim)', marginLeft: 4, fontSize: '0.72rem' }}>{p.rating}</span>
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  {result ? <PriceTag price={result.new_price} original={p.store_price} /> : <span style={{ fontWeight: 800, fontSize: '1.1rem' }}>${p.store_price.toFixed(2)}</span>}
                  <Sparkline data={p.history} />
                </div>

                {p.competitor && (
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    {Object.entries(p.competitor.all_prices || {}).map(([store, price]) => {
                      const isLowest = price === Math.min(...Object.values(p.competitor!.all_prices))
                      return (
                        <span key={store} style={{
                          fontSize: '0.68rem', padding: '2px 6px', borderRadius: 'var(--radius-xs)',
                          background: isLowest ? 'var(--success-glow)' : 'var(--glass)',
                          color: isLowest ? 'var(--success)' : 'var(--text-dim)',
                          border: `1px solid ${isLowest ? 'rgba(16,185,129,0.15)' : 'var(--glass-border)'}`,
                          fontWeight: isLowest ? 700 : 400,
                        }}>
                          {store} ${price.toFixed(2)}
                        </span>
                      )
                    })}
                  </div>
                )}

                <div style={{ display: 'flex', gap: 6 }}>
                  {!result ? (
                    <button className="btn btn-primary" onClick={e => { e.stopPropagation(); handleCheck(p) }} disabled={checking === p.id}
                      style={{ flex: 1, height: 32, fontSize: '0.78rem' }}>
                      {checking === p.id ? <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span className="spinner" /> Scanning...</span> : '\uD83D\uDD0D Check Price'}
                    </button>
                  ) : result.status === 'approved' ? (
                    <button className="btn btn-success" onClick={e => { e.stopPropagation(); handleApply(result.id, p.id) }} disabled={applying === result.id}
                      style={{ flex: 1, height: 32, fontSize: '0.78rem' }}>
                      {applying === result.id ? 'Applying...' : `\u2713 Apply -$${result.discount_amount.toFixed(2)}`}
                    </button>
                  ) : result.status === 'applied' ? (
                    <span style={{ flex: 1, textAlign: 'center', color: 'var(--success)', fontWeight: 600, fontSize: '0.82rem', padding: '6px' }}>
                      {"\u2713"} Applied {"\u2014"} ${result.new_price.toFixed(2)}
                    </span>
                  ) : (
                    <span style={{ flex: 1, textAlign: 'center', color: 'var(--text-dim)', fontSize: '0.78rem', padding: '6px' }}>No better price found</span>
                  )}
                </div>

                <AnimatePresence>
                  {isSelected && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                      style={{ overflow: 'hidden', borderTop: '1px solid var(--glass-border)', paddingTop: 8 }}>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', marginBottom: 6 }}>{p.description}</p>
                      {p.tags.length > 0 && (
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                          {p.tags.map(t => <span key={t} className="tag" style={{ fontSize: '0.65rem' }}>{t}</span>)}
                        </div>
                      )}
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
