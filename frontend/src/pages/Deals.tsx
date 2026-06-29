import { useState } from 'react'
import { getPromotions, optimizeCart } from '../services/api'
import type { CartItem, DealResult, Promotion } from '../types'

const TIERS = ['bronze', 'silver', 'gold', 'platinum'] as const

const SAMPLE_PRODUCTS: { product_id: string; sku: string; name: string; price: number; category: string }[] = [
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
      if (existing) {
        return prev.map(i => i.product_id === p.product_id ? { ...i, quantity: i.quantity + 1 } : i)
      }
      return [...prev, { ...p, quantity: 1 }]
    })
  }

  const removeItem = (productId: string) => {
    setCartItems(prev => {
      const existing = prev.find(i => i.product_id === productId)
      if (existing && existing.quantity > 1) {
        return prev.map(i => i.product_id === productId ? { ...i, quantity: i.quantity - 1 } : i)
      }
      return prev.filter(i => i.product_id !== productId)
    })
  }

  const subtotal = cartItems.reduce((s, i) => s + i.price * i.quantity, 0)

  const handleOptimize = async () => {
    if (cartItems.length === 0) return
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const res = await optimizeCart({
        user_id: userId,
        items: cartItems,
        loyalty_tier: TIERS[tier],
        budget: budget ? parseFloat(budget) : undefined,
      })
      setResult(res)
    } catch {
      setError('Failed to optimize cart. Please try again.')
      setResult(null)
    }
    setLoading(false)
  }

  const handleShowPromos = async () => {
    if (promotions) { setShowPromos(!showPromos); return }
    setError(null)
    try {
      const res = await getPromotions()
      setPromotions(res)
      setShowPromos(true)
    } catch { setError('Failed to load promotions') }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">DealAgent</h1>
          <p className="page-subtitle">Maximize savings with smart discount stacking</p>
        </div>
        <button className="btn" onClick={handleShowPromos} style={{ height: 36 }} aria-label={showPromos ? 'Hide promotions' : 'View active promotions'}>
          {showPromos ? 'Hide Promotions' : 'View Active Promotions'}
        </button>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {showPromos && promotions && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <p className="section-title" style={{ marginBottom: '0.75rem' }}>Active Promotions</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {promotions.map(p => (
              <span key={p.id} className="tag" style={{
                background: p.stackable ? '#1a3a2a' : '#3a1a2a',
                color: p.stackable ? '#2bd47c' : '#ef5566',
                padding: '4px 10px', borderRadius: 6, fontSize: '0.8rem',
              }} aria-label={`${p.name}: ${p.value}${p.type === 'percentage' || p.type === 'category_markdown' ? '%' : '$'}`}>
                {p.stackable ? '↕' : '⊘'} {p.name} {p.value}{p.type === 'percentage' || p.type === 'category_markdown' ? '%' : '$'}
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
            <input id="deal-userid" className="input" value={userId} onChange={e => setUserId(e.target.value)} aria-label="User ID" />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="deal-tier">Loyalty Tier</label>
            <select id="deal-tier" className="input" value={tier} onChange={e => setTier(Number(e.target.value))} aria-label="Loyalty tier">
              {TIERS.map((t, i) => <option key={t} value={i}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="deal-budget">Budget (optional)</label>
            <input id="deal-budget" className="input" type="number" min="0" step="0.01"
              value={budget} onChange={e => setBudget(e.target.value)}
              placeholder="e.g. 500" aria-label="Budget" />
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.5rem' }}>
        <div className="card" style={{ flex: 1 }}>
          <p className="section-title" style={{ marginBottom: '0.75rem' }}>Add Items to Cart</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {SAMPLE_PRODUCTS.map(p => (
              <div key={p.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                <span>{p.name} — <strong>${p.price}</strong></span>
                <button className="btn" onClick={() => addItem(p)} style={{ height: 28, fontSize: '0.8rem', padding: '0 10px' }}
                  aria-label={`Add ${p.name} to cart`}>
                  + Add
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="card" style={{ flex: 1 }}>
          <p className="section-title" style={{ marginBottom: '0.75rem' }}>
            Your Cart <span style={{ color: '#a0aec0', fontWeight: 400 }}>({cartItems.reduce((s, i) => s + i.quantity, 0)} items)</span>
          </p>
          {cartItems.length === 0 ? (
            <p style={{ color: '#6b7280', fontSize: '0.85rem' }}>Cart is empty. Add products to get started.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
              {cartItems.map(item => (
                <div key={item.product_id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                  <span>{item.name} x{item.quantity} — <strong>${(item.price * item.quantity).toFixed(2)}</strong></span>
                  <button className="btn btn-danger" onClick={() => removeItem(item.product_id)} style={{ height: 24, fontSize: '0.75rem', padding: '0 8px' }}
                    aria-label={`Remove ${item.name}`}>
                    ✕
                  </button>
                </div>
              ))}
              <hr style={{ borderColor: '#2d3748', margin: '0.3rem 0' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600 }}>
                <span>Subtotal:</span>
                <span>${subtotal.toFixed(2)}</span>
              </div>
            </div>
          )}
          <button className="btn btn-primary" onClick={handleOptimize}
            disabled={cartItems.length === 0 || loading}
            style={{ marginTop: '0.75rem', width: '100%' }} aria-label="Optimize cart">
            {loading ? 'Analyzing...' : 'Optimize My Cart'}
          </button>
        </div>
      </div>

      {loading && !result && (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }} role="status">
          <p style={{ color: 'var(--text-dim)' }}>Analyzing your cart for the best deals...</p>
        </div>
      )}

      {result && (
        <div className="card animate-in" style={{ borderLeft: '4px solid #2bd47c' }}>
          <p className="section-title" style={{ marginBottom: '0.5rem' }}>DealAgent Results</p>
          <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>{result.message}</p>
          <pre style={{
            background: '#1a202c', padding: '1rem', borderRadius: 8,
            fontSize: '0.85rem', lineHeight: '1.6', whiteSpace: 'pre-wrap',
            fontFamily: 'monospace',
          }}>
            {result.savings_breakdown}
          </pre>
          {result.applied_discounts.length > 0 && (
            <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {result.applied_discounts.map(d => (
                <span key={d.promotion_id} className="tag" style={{
                  background: '#1a3a2a', color: '#2bd47c',
                  padding: '4px 10px', borderRadius: 6, fontSize: '0.8rem',
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
