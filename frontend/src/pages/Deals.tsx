import { useState } from 'react'
import { getPromotions, optimizeCart } from '../services/api'
import type { CartItem, DealResult, Promotion } from '../types'

const TIERS = ['bronze', 'silver', 'gold', 'platinum'] as const
const TIER_COLORS = ['#cd7f32', '#c0c0c0', '#ffd700', '#e5e4e2']

const SAMPLE_PRODUCTS = [
  { product_id: 'p1', sku: 'SKU-WH001', name: 'Wireless Headphones', price: 249.99, category: 'Electronics' },
  { product_id: 'p2', sku: 'SKU-RS001', name: 'Running Shoes', price: 129.99, category: 'Sports' },
  { product_id: 'p3', sku: 'SKU-CM001', name: 'Coffee Maker', price: 79.99, category: 'Home' },
  { product_id: 'p4', sku: 'SKU-SW001', name: 'Smart Watch', price: 199.99, category: 'Electronics' },
  { product_id: 'p5', sku: 'SKU-LJ001', name: 'Leather Jacket', price: 349.99, category: 'Fashion' },
  { product_id: 'p7', sku: 'SKU-BS001', name: 'Bluetooth Speaker', price: 59.99, category: 'Electronics' },
]

export default function Deals() {
  const [userId, setUserId] = useState('user_001')
  const [tier, setTier] = useState<number>(0)
  const [budget, setBudget] = useState('')
  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<DealResult | null>(null)
  const [promotions, setPromotions] = useState<Promotion[] | null>(null)
  const [showPromos, setShowPromos] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addItem = (p: typeof SAMPLE_PRODUCTS[0]) => {
    setCartItems(prev => {
      const existing = prev.find(i => i.product_id === p.product_id)
      if (existing) return prev.map(i => i.product_id === p.product_id ? { ...i, quantity: i.quantity + 1 } : i)
      return [...prev, { ...p, quantity: 1 }]
    })
  }

  const removeItem = (productId: string) => {
    setCartItems(prev => {
      const existing = prev.find(i => i.product_id === productId)
      if (existing && existing.quantity > 1) return prev.map(i => i.product_id === productId ? { ...i, quantity: i.quantity - 1 } : i)
      return prev.filter(i => i.product_id !== productId)
    })
  }

  const subtotal = cartItems.reduce((s, i) => s + i.price * i.quantity, 0)

  const handleOptimize = async () => {
    if (cartItems.length === 0) return
    setLoading(true); setResult(null); setError(null)
    try {
      const res = await optimizeCart({
        user_id: userId, items: cartItems, loyalty_tier: TIERS[tier],
        budget: budget ? parseFloat(budget) : undefined,
      })
      setResult(res)
    } catch { setError('Failed to optimize cart.'); setResult(null) }
    setLoading(false)
  }

  const handleShowPromos = async () => {
    if (promotions) { setShowPromos(!showPromos); return }
    setError(null)
    try { const res = await getPromotions(); setPromotions(res); setShowPromos(true) }
    catch { setError('Failed to load promotions') }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">DealAgent</h1>
          <p className="page-subtitle">Maximize savings with smart discount stacking</p>
        </div>
        <button className="btn btn-ghost" onClick={handleShowPromos} style={{ height: 38 }}>
          {showPromos ? 'Hide Promotions' : 'View Active Promotions'}
        </button>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {showPromos && promotions && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <p className="section-title" style={{ marginBottom: '0.75rem' }}>Active Promotions</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
            {promotions.map(p => (
              <span key={p.id} className="tag" style={{
                background: p.stackable ? 'var(--success-glow)' : 'var(--danger-glow)',
                color: p.stackable ? 'var(--success)' : 'var(--danger)',
                border: `1px solid ${p.stackable ? 'rgba(16,185,129,0.15)' : 'rgba(244,63,94,0.15)'}`,
              }}>
                {p.stackable ? '\u2195' : '\u2298'} {p.name} {p.value}{p.type === 'percentage' || p.type === 'category_markdown' ? '%' : '$'}
                {p.min_purchase ? ` (min $${p.min_purchase})` : ''}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <p className="section-title" style={{ marginBottom: '0.75rem' }}>Session Config</p>
        <div className="form-row">
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="deal-userid">User ID</label>
            <input id="deal-userid" className="input" value={userId} onChange={e => setUserId(e.target.value)} />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="deal-tier">Loyalty Tier</label>
            <select id="deal-tier" className="input" value={tier} onChange={e => setTier(Number(e.target.value))}>
              {TIERS.map((t, i) => <option key={t} value={i}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="deal-budget">Budget (optional)</label>
            <input id="deal-budget" className="input" type="number" min="0" step="0.01"
              value={budget} onChange={e => setBudget(e.target.value)} placeholder="e.g. 500" />
          </div>
        </div>
        <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.35rem' }}>
          {TIERS.map((t, i) => (
            <span key={t} style={{
              padding: '4px 10px', borderRadius: 'var(--radius-xs)', fontSize: '0.72rem', fontWeight: 600,
              background: i === tier ? 'var(--primary-glow)' : 'var(--glass)',
              color: i === tier ? 'var(--primary)' : 'var(--text-dim)',
              border: `1px solid ${i === tier ? 'rgba(129,140,248,0.2)' : 'var(--glass-border)'}`,
              cursor: 'pointer', transition: 'var(--transition)',
            }} onClick={() => setTier(i)}>
              <span style={{ color: TIER_COLORS[i], marginRight: 4 }}>{'\u2605'}</span> {t}
            </span>
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1.25rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ flex: 1 }}>
          <p className="section-title" style={{ marginBottom: '0.75rem' }}>Add Items</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {SAMPLE_PRODUCTS.map(p => (
              <div key={p.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem', padding: '6px 0' }}>
                <span style={{ color: 'var(--text-muted)' }}>{p.name} <strong style={{ color: 'var(--text)' }}>${p.price}</strong></span>
                <button className="btn btn-ghost" onClick={() => addItem(p)} style={{ height: 26, fontSize: '0.72rem', padding: '0 8px' }}>+</button>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ flex: 1 }}>
          <p className="section-title" style={{ marginBottom: '0.75rem' }}>
            Cart <span style={{ color: 'var(--text-dim)', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>({cartItems.reduce((s, i) => s + i.quantity, 0)} items)</span>
          </p>
          {cartItems.length === 0 ? (
            <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem' }}>Cart is empty. Add products to get started.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {cartItems.map(item => (
                <div key={item.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem', padding: '4px 0' }}>
                  <span style={{ color: 'var(--text-muted)' }}>{item.name} x{item.quantity} <strong style={{ color: 'var(--text)' }}>${(item.price * item.quantity).toFixed(2)}</strong></span>
                  <button className="btn btn-danger" onClick={() => removeItem(item.product_id)}
                    style={{ height: 22, fontSize: '0.7rem', padding: '0 6px' }}>{"\u2715"}</button>
                </div>
              ))}
              <div style={{ borderTop: '1px solid var(--glass-border)', marginTop: 4, paddingTop: 6, display: 'flex', justifyContent: 'space-between', fontWeight: 700, fontSize: '0.9rem' }}>
                <span>Subtotal</span>
                <span style={{ color: 'var(--primary)' }}>${subtotal.toFixed(2)}</span>
              </div>
            </div>
          )}
          <button className="btn btn-primary" onClick={handleOptimize} disabled={cartItems.length === 0 || loading}
            style={{ marginTop: '0.75rem', width: '100%', height: 40 }}>
            {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}><span className="spinner" /> Analyzing...</span> : 'Optimize My Cart'}
          </button>
        </div>
      </div>

      {loading && !result && (
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }} role="status">
          <span className="spinner" style={{ margin: '0 auto', display: 'block' }} />
          <p style={{ color: 'var(--text-dim)', marginTop: '0.75rem' }}>Analyzing your cart for the best deals...</p>
        </div>
      )}

      {result && (
        <div className="card animate-in" style={{ borderLeft: '3px solid var(--success)' }}>
          <p className="section-title" style={{ marginBottom: '0.5rem' }}>DealAgent Results</p>
          <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-muted)' }}>{result.message}</p>
          <div style={{
            background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: 'var(--radius-sm)',
            fontSize: '0.82rem', lineHeight: 1.6, whiteSpace: 'pre-wrap',
            fontFamily: "'JetBrains Mono', monospace", color: 'var(--text-muted)',
            border: '1px solid var(--glass-border)',
          }}>
            {result.savings_breakdown}
          </div>
          {result.applied_discounts.length > 0 && (
            <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
              {result.applied_discounts.map(d => (
                <span key={d.promotion_id} className="tag" style={{
                  background: 'var(--success-glow)', color: 'var(--success)',
                  border: '1px solid rgba(16,185,129,0.15)',
                }}>
                  {d.promotion_name}: -${d.discount_amount.toFixed(2)}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
