import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getPriceMatchProducts, checkPriceMatch, applyDiscount, getPriceAlerts } from '../services/api'
import type { PriceMatchProduct, DiscountResult, PriceDropAlert } from '../types'

const STORE_LOGOS: Record<string, { color: string; label: string }> = {
  Amazon: { color: '#ff9900', label: 'Amazon' },
  BestBuy: { color: '#0046be', label: 'Best Buy' },
  Walmart: { color: '#0071ce', label: 'Walmart' },
  Target: { color: '#cc0000', label: 'Target' },
  eBay: { color: '#0064d2', label: 'eBay' },
}

function Sparkline({ data, width = 120, height = 32 }: { data: { price: number }[]; width?: number; height?: number }) {
  if (!data.length) return null
  const prices = data.map(d => d.price)
  const min = Math.min(...prices) * 0.98
  const max = Math.max(...prices) * 1.02
  const range = max - min || 1
  const stepX = width / (prices.length - 1)
  const points = prices.map((p, i) => `${i * stepX},${height - ((p - min) / range) * (height - 4) - 2}`).join(' ')
  const trend = prices[prices.length - 1] >= prices[0]
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline points={points} fill="none" stroke={trend ? '#10b981' : '#ef5566'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      {prices.map((p, i) => (
        <circle key={i} cx={i * stepX} cy={height - ((p - min) / range) * (height - 4) - 2} r="2" fill={trend ? '#10b981' : '#ef5566'} opacity={i === prices.length - 1 ? 1 : 0.3} />
      ))}
    </svg>
  )
}

function PriceTag({ price, original }: { price: number; original?: number }) {
  if (original && original > price) {
    const saved = ((original - price) / original * 100).toFixed(1)
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <span style={{ textDecoration: 'line-through', color: '#6b7280', fontSize: '0.8rem' }}>${original.toFixed(2)}</span>
        <span style={{ fontWeight: 700, fontSize: '1.1rem', color: '#10b981' }}>${price.toFixed(2)}</span>
        <span style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981', padding: '1px 6px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 600 }}>-{saved}%</span>
      </span>
    )
  }
  return <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>${price.toFixed(2)}</span>
}

export default function PriceMatch() {
  const [products, setProducts] = useState<PriceMatchProduct[]>([])
  const [loading, setLoading] = useState(true)
  const [checking, setChecking] = useState<string | null>(null)
  const [results, setResults] = useState<Record<string, DiscountResult>>({})
  const [applying, setApplying] = useState<string | null>(null)
  const [alerts, setAlerts] = useState<{ product_id: string; product_name: string; alerts: PriceDropAlert[] }[]>([])
  const [showAlerts, setShowAlerts] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const userId = 'web_user_001'

  useEffect(() => {
    getPriceMatchProducts().then(data => { setProducts(data); setLoading(false) }).catch(() => setLoading(false))
    getPriceAlerts(3).then(setAlerts).catch(() => {})
  }, [])

  const handleCheck = async (p: PriceMatchProduct) => {
    setChecking(p.id)
    try {
      const res = await checkPriceMatch(p.id, p.sku, p.store_price, userId)
      if (res.discount) setResults(prev => ({ ...prev, [p.id]: res.discount }))
    } catch { /* ignore */ }
    setChecking(null)
  }

  const handleApply = async (discountId: string, productId: string) => {
    setApplying(discountId)
    try {
      const updated = await applyDiscount(discountId)
      setResults(prev => ({ ...prev, [productId]: updated }))
    } catch { /* ignore */ }
    setApplying(null)
  }

  const totalSavings = Object.values(results).reduce((s, r) => s + (r.status === 'approved' || r.status === 'applied' ? r.discount_amount : 0), 0)
  const approvedCount = Object.values(results).filter(r => r.status === 'approved' || r.status === 'applied').length

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="page-title">Price Match Agent</motion.h1>
          <p className="page-subtitle">Scan competitor pricing across 5 retailers and unlock exclusivesavings</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          {alerts.length > 0 && (
            <button className="btn" onClick={() => setShowAlerts(!showAlerts)} style={{ height: 36, position: 'relative' }}>
              <span>🔔</span> Alerts
              <span style={{ position: 'absolute', top: -4, right: -4, background: '#ef5566', color: '#fff', borderRadius: '50%', width: 18, height: 18, fontSize: '0.65rem', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 700 }}>
                {alerts.length}
              </span>
            </button>
          )}
        </div>
      </div>

      <AnimatePresence>
        {showAlerts && alerts.length > 0 && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="card" style={{ marginBottom: '1.5rem', overflow: 'hidden', borderLeft: '4px solid #f59e0b' }}>
            <p className="section-title" style={{ marginBottom: '0.5rem' }}>📉 Price Drop Alerts</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {alerts.map(a => a.alerts.slice(0, 2).map((alert, i) => (
                <div key={`${a.product_id}-${i}`} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                  <span style={{ fontWeight: 500 }}>{a.product_name}</span>
                  <span style={{ color: '#10b981' }}>${alert.from.toFixed(2)} → ${alert.to.toFixed(2)} <strong style={{ background: 'rgba(16,185,129,0.15)', padding: '1px 6px', borderRadius: 4 }}>-{alert.drop_pct}%</strong></span>
                </div>
              )))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {approvedCount > 0 && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '0.75rem', marginBottom: '1.5rem' }}>
          <div className="card" style={{ borderLeft: '4px solid #10b981' }}>
            <span style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: 500 }}>Total Savings</span>
            <strong style={{ fontSize: '1.5rem', color: '#10b981' }}>${totalSavings.toFixed(2)}</strong>
          </div>
          <div className="card" style={{ borderLeft: '4px solid #818cf8' }}>
            <span style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: 500 }}>Price Matches</span>
            <strong style={{ fontSize: '1.5rem', color: '#818cf8' }}>{approvedCount}/{Object.keys(results).length}</strong>
          </div>
          <div className="card" style={{ borderLeft: '4px solid #f59e0b' }}>
            <span style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: 500 }}>Products Scanned</span>
            <strong style={{ fontSize: '1.5rem', color: '#f59e0b' }}>{products.length}</strong>
          </div>
          <div className="card" style={{ borderLeft: '4px solid #f43f5e' }}>
            <span style={{ fontSize: '0.75rem', color: '#6b7280', fontWeight: 500 }}>Avg Discount</span>
            <strong style={{ fontSize: '1.5rem', color: '#f43f5e' }}>{approvedCount > 0 ? `${(totalSavings / approvedCount).toFixed(2)}` : '$0'}</strong>
          </div>
        </motion.div>
      )}

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '1rem' }}>
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="card animate-in" style={{ height: 260, background: 'linear-gradient(135deg, var(--surface2) 25%, var(--surface) 50%, var(--surface2) 75%)', backgroundSize: '200% 100%', animation: 'shimmer 2s infinite' }} />
          ))}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1rem' }}>
          {products.map((p, i) => {
            const result = results[p.id]
            const isSelected = selected === p.id
            return (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="card animate-in"
                style={{
                  cursor: 'pointer',
                  borderColor: result?.status === 'approved' || result?.status === 'applied' ? '#10b981' : isSelected ? '#818cf8' : undefined,
                  borderLeft: result?.status === 'approved' || result?.status === 'applied' ? '4px solid #10b981' : result?.status === 'declined' ? '4px solid #6b7280' : undefined,
                }}
                onClick={() => setSelected(isSelected ? null : p.id)}
                layout
              >
                <div className="card-header">
                  <div>
                    <h3 style={{ fontSize: '0.95rem', margin: 0 }}>{p.name}</h3>
                    <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>{p.category}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <span style={{ color: '#f59e0b', fontSize: '0.8rem' }}>{'★'.repeat(Math.round(p.rating))}</span>
                    <span style={{ color: '#6b7280', fontSize: '0.75rem' }}>{p.rating}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  {result ? (
                    <PriceTag price={result.new_price} original={p.store_price} />
                  ) : (
                    <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>${p.store_price.toFixed(2)}</span>
                  )}
                  <Sparkline data={p.history} width={100} height={28} />
                </div>

                {p.competitor && (
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
                    {Object.entries(p.competitor.all_prices || {}).map(([store, price]) => {
                      const storeInfo = STORE_LOGOS[store] || { color: '#6b7280', label: store }
                      const isLowest = price === Math.min(...Object.values(p.competitor!.all_prices))
                      return (
                        <span key={store} style={{
                          fontSize: '0.7rem', padding: '2px 6px', borderRadius: 4,
                          background: isLowest ? 'rgba(16,185,129,0.15)' : 'var(--surface2)',
                          color: isLowest ? '#10b981' : '#9ca3af',
                          border: `1px solid ${isLowest ? 'rgba(16,185,129,0.3)' : 'var(--border)'}`,
                          fontWeight: isLowest ? 600 : 400,
                        }}>
                          {storeInfo.label} ${price.toFixed(2)}
                        </span>
                      )
                    })}
                  </div>
                )}

                <div style={{ display: 'flex', gap: 6, marginTop: 8 }}>
                  {!result ? (
                    <button className="btn btn-primary" onClick={e => { e.stopPropagation(); handleCheck(p) }} disabled={checking === p.id} style={{ flex: 1, height: 32, fontSize: '0.8rem' }}>
                      {checking === p.id ? <><span className="status-dot" style={{ animation: 'pulse-dot 1.5s infinite' }} /> Scanning...</> : '🔍 Check Price'}
                    </button>
                  ) : result.status === 'approved' ? (
                    <button className="btn btn-success" onClick={e => { e.stopPropagation(); handleApply(result.id, p.id) }} disabled={applying === result.id} style={{ flex: 1, height: 32, fontSize: '0.8rem' }}>
                      {applying === result.id ? 'Applying...' : `✅ Apply -$${result.discount_amount.toFixed(2)}`}
                    </button>
                  ) : result.status === 'applied' ? (
                    <span style={{ flex: 1, textAlign: 'center', color: '#10b981', fontWeight: 600, fontSize: '0.85rem', padding: '6px' }}>
                      ✅ Discount Applied — ${result.new_price.toFixed(2)}
                    </span>
                  ) : (
                    <span style={{ flex: 1, textAlign: 'center', color: '#6b7280', fontSize: '0.8rem', padding: '6px' }}>
                      ❌ No better price found
                    </span>
                  )}
                </div>

                {result && result.status !== 'declined' && (
                  <div style={{ fontSize: '0.75rem', color: '#6b7280', display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                    <span>Competitor: <strong style={{ color: '#818cf8' }}>{result.competitor_store}</strong> @ ${result.competitor_price.toFixed(2)}</span>
                    <span>{result.status === 'applied' ? 'Applied' : 'Approved'}</span>
                  </div>
                )}

                <AnimatePresence>
                  {isSelected && (
                    <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} style={{ overflow: 'hidden', borderTop: '1px solid var(--border)', marginTop: 8, paddingTop: 8 }}>
                      <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginBottom: 6 }}>{p.description}</p>
                      {p.alerts.length > 0 && (
                        <div style={{ fontSize: '0.75rem' }}>
                          <span style={{ color: '#f59e0b' }}>📉 Price drops detected:</span>
                          {p.alerts.slice(0, 3).map((a, j) => (
                            <div key={j} style={{ color: '#6b7280', marginTop: 2 }}>${a.from.toFixed(2)} → ${a.to.toFixed(2)} ({a.drop_pct}% drop)</div>
                          ))}
                        </div>
                      )}
                      {p.tags.length > 0 && (
                        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 6 }}>
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

      <style>{`
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }
      `}</style>
    </div>
  )
}
