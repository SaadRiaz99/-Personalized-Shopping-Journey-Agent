import { useState, useEffect, useRef } from 'react'
import {
  getBudgetSummary,
  getBudgetLimits,
  getBudgetEntries,
  setBudgetLimit,
  trackBudgetEntry,
  checkBudget,
  deleteBudgetEntry,
  deleteBudgetLimit,
} from '../services/api'
import type { SpendingSummary, BudgetLimit, BudgetEntry, BudgetCheckResult } from '../types'

const PERIODS = ['daily', 'weekly', 'monthly'] as const
const CATEGORIES = ['Electronics', 'Fashion', 'Sports', 'Home', 'Beauty', 'Books', 'Toys & Games', 'Health & Wellness', 'Outdoor', 'Office Supplies', 'Automotive', 'Baby & Kids', 'Music', 'Pet Supplies']

const SAMPLE_ITEMS = [
  { product_id: 'p1', product_name: 'Wireless Headphones', category: 'Electronics', amount: 249.99, icon: '🎧' },
  { product_id: 'p2', product_name: 'Running Shoes', category: 'Sports', amount: 129.99, icon: '👟' },
  { product_id: 'p3', product_name: 'Coffee Maker', category: 'Home', amount: 79.99, icon: '☕' },
  { product_id: 'p5', product_name: 'Leather Jacket', category: 'Fashion', amount: 349.99, icon: '🧥' },
  { product_id: 'p7', product_name: 'Bluetooth Speaker', category: 'Electronics', amount: 59.99, icon: '🔊' },
]

const GRADIENT_COLORS = [
  'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
  'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
  'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
  'linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%)',
  'linear-gradient(135deg, #fccb90 0%, #d57eeb 100%)',
]

export default function BudgetTracker() {
  const [userId, setUserId] = useState('user_001')
  const [period, setPeriod] = useState<string>('monthly')
  const [summary, setSummary] = useState<SpendingSummary | null>(null)
  const [limits, setLimits] = useState<BudgetLimit[]>([])
  const [entries, setEntries] = useState<BudgetEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [limitPeriod, setLimitPeriod] = useState<string>('monthly')
  const [limitAmount, setLimitAmount] = useState('')
  const [limitCategory, setLimitCategory] = useState('')
  const [settingLimit, setSettingLimit] = useState(false)

  const [checkResult, setCheckResult] = useState<BudgetCheckResult | null>(null)
  const [checkItem, setCheckItem] = useState<string>('')
  const [checking, setChecking] = useState(false)

  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!heroRef.current) return
      const rect = heroRef.current.getBoundingClientRect()
      const x = ((e.clientX - rect.left) / rect.width - 0.5) * 20
      const y = ((e.clientY - rect.top) / rect.height - 0.5) * 20
      heroRef.current.style.setProperty('--mx', `${x}px`)
      heroRef.current.style.setProperty('--my', `${y}px`)
    }
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  const loadAll = async () => {
    setLoading(true)
    setError(null)
    try {
      const [s, l, e] = await Promise.all([
        getBudgetSummary(userId, period),
        getBudgetLimits(userId),
        getBudgetEntries(userId, period),
      ])
      setSummary(s)
      setLimits(l)
      setEntries(e)
    } catch {
      setError('Failed to load budget data')
    }
    setLoading(false)
  }

  // loadAll is intentionally re-run only when the selected user or period changes.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadAll() }, [userId, period])

  const handleSetLimit = async () => {
    if (!limitAmount) return
    setSettingLimit(true)
    setError(null)
    try {
      await setBudgetLimit({
        user_id: userId,
        period: limitPeriod,
        limit_amount: parseFloat(limitAmount),
        category: limitCategory || undefined,
      })
      setLimitAmount('')
      setLimitCategory('')
      const l = await getBudgetLimits(userId)
      setLimits(l)
    } catch {
      setError('Failed to set budget limit')
    }
    setSettingLimit(false)
  }

  const handleTrackEntry = async (item: typeof SAMPLE_ITEMS[0]) => {
    setError(null)
    try {
      await trackBudgetEntry({ user_id: userId, product_id: item.product_id, product_name: item.product_name, category: item.category, amount: item.amount, quantity: 1 })
      await loadAll()
    } catch {
      setError('Failed to track entry')
    }
  }

  const handleCheckBudget = async () => {
    if (!checkItem) return
    const item = SAMPLE_ITEMS.find(i => i.product_id === checkItem)
    if (!item) return
    setChecking(true)
    setError(null)
    try {
      const result = await checkBudget({
        user_id: userId,
        product_id: item.product_id,
        product_name: item.product_name,
        category: item.category,
        amount: item.amount,
      })
      setCheckResult(result)
    } catch {
      setError('Failed to check budget')
    }
    setChecking(false)
  }

  const handleDeleteEntry = async (id: string) => {
    try {
      await deleteBudgetEntry(id)
      await loadAll()
    } catch {
      setError('Failed to delete entry')
    }
  }

  const handleDeleteLimit = async (id: string) => {
    try {
      await deleteBudgetLimit(id)
      const l = await getBudgetLimits(userId)
      setLimits(l)
    } catch {
      setError('Failed to delete limit')
    }
  }

  const spentPct = summary && summary.limits.length > 0
    ? Math.min((summary.total_spent / summary.limits[0].limit_amount) * 100, 100)
    : 0

  return (
    <div className="bt-root">
      <style>{`
        .bt-root { --mx: 0px; --my: 0px; }

        .bt-hero {
          position: relative;
          padding: 3rem 2.5rem 2.5rem;
          border-radius: 24px;
          background: linear-gradient(145deg, rgba(15,17,30,0.95) 0%, rgba(22,25,44,0.9) 100%);
          border: 1px solid rgba(255,255,255,0.04);
          backdrop-filter: blur(40px);
          overflow: hidden;
          margin-bottom: 2rem;
          transition: transform 0.4s cubic-bezier(0.25,0.46,0.45,0.94);
        }
        .bt-hero::before {
          content: '';
          position: absolute;
          top: -50%;
          left: -50%;
          width: 200%;
          height: 200%;
          background: radial-gradient(circle at calc(50% + var(--mx)) calc(50% + var(--my)),
            rgba(129,140,248,0.06) 0%, transparent 50%);
          pointer-events: none;
          transition: background 0.3s ease;
        }
        .bt-hero::after {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(129,140,248,0.3), transparent);
        }
        .bt-hero-label {
          font-size: 0.7rem;
          font-weight: 700;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: rgba(129,140,248,0.6);
          margin-bottom: 0.5rem;
        }
        .bt-hero-title {
          font-size: clamp(2rem, 4vw, 3.2rem);
          font-weight: 800;
          letter-spacing: -0.04em;
          line-height: 1.1;
          background: linear-gradient(135deg, #f8fafc 0%, #818cf8 50%, #c084fc 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          margin-bottom: 0.5rem;
        }
        .bt-hero-sub {
          font-size: 0.95rem;
          color: rgba(148,163,184,0.7);
          font-weight: 400;
          max-width: 400px;
        }

        .bt-glass {
          background: rgba(15,17,30,0.6);
          border: 1px solid rgba(255,255,255,0.04);
          border-radius: 16px;
          padding: 1.5rem;
          backdrop-filter: blur(24px);
          transition: all 0.4s cubic-bezier(0.25,0.46,0.45,0.94);
          position: relative;
          overflow: hidden;
        }
        .bt-glass:hover {
          border-color: rgba(255,255,255,0.08);
          box-shadow: 0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(255,255,255,0.02);
          transform: translateY(-2px);
        }
        .bt-glass::after {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 1px;
          background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
        }

        .bt-section-label {
          font-size: 0.65rem;
          font-weight: 700;
          letter-spacing: 0.15em;
          text-transform: uppercase;
          color: rgba(148,163,184,0.5);
          margin-bottom: 1rem;
        }

        .bt-stat-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1.25rem;
          margin-bottom: 2rem;
        }
        .bt-stat-card {
          position: relative;
          padding: 1.75rem;
          border-radius: 20px;
          background: rgba(15,17,30,0.5);
          border: 1px solid rgba(255,255,255,0.03);
          backdrop-filter: blur(20px);
          overflow: hidden;
          transition: all 0.4s cubic-bezier(0.25,0.46,0.45,0.94);
        }
        .bt-stat-card:hover {
          transform: translateY(-4px) scale(1.01);
          border-color: rgba(255,255,255,0.08);
          box-shadow: 0 20px 60px rgba(0,0,0,0.4);
        }
        .bt-stat-card::before {
          content: '';
          position: absolute;
          top: 0; left: 0;
          width: 100%; height: 3px;
          border-radius: 20px 20px 0 0;
        }
        .bt-stat-card:nth-child(1)::before { background: linear-gradient(90deg, #667eea, #764ba2); }
        .bt-stat-card:nth-child(2)::before { background: linear-gradient(90deg, #43e97b, #38f9d7); }
        .bt-stat-card:nth-child(3)::before { background: linear-gradient(90deg, #fa709a, #fee140); }
        .bt-stat-icon {
          width: 40px; height: 40px;
          border-radius: 12px;
          display: flex; align-items: center; justify-content: center;
          font-size: 1.1rem;
          margin-bottom: 1rem;
        }
        .bt-stat-card:nth-child(1) .bt-stat-icon { background: rgba(102,126,234,0.15); }
        .bt-stat-card:nth-child(2) .bt-stat-icon { background: rgba(67,233,123,0.15); }
        .bt-stat-card:nth-child(3) .bt-stat-icon { background: rgba(250,112,154,0.15); }
        .bt-stat-value {
          font-size: clamp(1.5rem, 2.5vw, 2.2rem);
          font-weight: 800;
          letter-spacing: -0.03em;
          line-height: 1;
          margin-bottom: 0.35rem;
        }
        .bt-stat-card:nth-child(1) .bt-stat-value { color: #a5b4fc; }
        .bt-stat-card:nth-child(2) .bt-stat-value { color: #6ee7b7; }
        .bt-stat-card:nth-child(3) .bt-stat-value { color: #fda4af; }
        .bt-stat-label {
          font-size: 0.7rem;
          font-weight: 600;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: rgba(148,163,184,0.5);
        }
        .bt-stat-sub {
          font-size: 0.75rem;
          color: rgba(148,163,184,0.4);
          margin-top: 0.25rem;
        }

        .bt-progress-ring {
          position: relative;
          width: 100%;
          height: 6px;
          background: rgba(255,255,255,0.03);
          border-radius: 99px;
          margin-top: 1rem;
          overflow: hidden;
        }
        .bt-progress-fill {
          height: 100%;
          border-radius: 99px;
          background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
          transition: width 1s cubic-bezier(0.25,0.46,0.45,0.94);
          box-shadow: 0 0 20px rgba(102,126,234,0.4);
          position: relative;
        }
        .bt-progress-fill::after {
          content: '';
          position: absolute;
          right: 0; top: -2px;
          width: 10px; height: 10px;
          border-radius: 50%;
          background: #fff;
          box-shadow: 0 0 12px rgba(102,126,234,0.8);
          opacity: 0.9;
        }

        .bt-grid-2 {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.25rem;
          margin-bottom: 2rem;
        }

        .bt-input {
          width: 100%;
          padding: 0.7rem 1rem;
          border-radius: 10px;
          border: 1px solid rgba(255,255,255,0.06);
          background: rgba(255,255,255,0.03);
          color: #f8fafc;
          font-size: 0.875rem;
          font-family: inherit;
          transition: all 0.3s ease;
          outline: none;
        }
        .bt-input:focus {
          border-color: rgba(129,140,248,0.4);
          box-shadow: 0 0 0 3px rgba(129,140,248,0.1), 0 0 20px rgba(129,140,248,0.05);
          background: rgba(255,255,255,0.05);
        }
        .bt-input::placeholder { color: rgba(148,163,184,0.3); }
        select.bt-input {
          cursor: pointer;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%2364748b'%3E%3Cpath d='M6 8L1 3h10z'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 0.75rem center;
          padding-right: 2rem;
        }
        select.bt-input option { background: #0f111e; color: #f8fafc; }

        .bt-label {
          display: block;
          font-size: 0.65rem;
          font-weight: 700;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: rgba(148,163,184,0.4);
          margin-bottom: 0.4rem;
        }
        .bt-field { margin-bottom: 0.85rem; }

        .bt-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          padding: 0.65rem 1.25rem;
          border: none;
          border-radius: 10px;
          font-weight: 600;
          font-size: 0.8rem;
          font-family: inherit;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.25,0.46,0.45,0.94);
          position: relative;
          overflow: hidden;
        }
        .bt-btn::before {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
          opacity: 0;
          transition: opacity 0.3s ease;
        }
        .bt-btn:hover::before { opacity: 1; }
        .bt-btn:active { transform: scale(0.97); }

        .bt-btn-primary {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: #fff;
          box-shadow: 0 4px 16px rgba(102,126,234,0.3);
          width: 100%;
        }
        .bt-btn-primary:hover:not(:disabled) {
          box-shadow: 0 6px 24px rgba(102,126,234,0.5);
          transform: translateY(-1px);
        }
        .bt-btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

        .bt-btn-ghost {
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.06);
          color: rgba(148,163,184,0.7);
          padding: 0.35rem 0.7rem;
          font-size: 0.7rem;
        }
        .bt-btn-ghost:hover {
          background: rgba(239,68,68,0.1);
          border-color: rgba(239,68,68,0.3);
          color: #f87171;
        }

        .bt-btn-sm {
          padding: 0.4rem 0.9rem;
          font-size: 0.75rem;
          border-radius: 8px;
        }

        .bt-tag-row {
          display: flex; gap: 0.4rem; flex-wrap: wrap;
        }
        .bt-tag {
          display: inline-flex; align-items: center; gap: 0.3rem;
          padding: 0.3rem 0.65rem;
          border-radius: 99px;
          font-size: 0.65rem;
          font-weight: 600;
          letter-spacing: 0.02em;
          border: 1px solid rgba(255,255,255,0.05);
          background: rgba(255,255,255,0.03);
          color: rgba(148,163,184,0.6);
          transition: all 0.3s ease;
        }
        .bt-tag:hover { border-color: rgba(255,255,255,0.1); color: #f8fafc; }
        .bt-tag-dot {
          width: 5px; height: 5px;
          border-radius: 50%;
          background: currentColor;
        }

        .bt-alert {
          padding: 1rem 1.25rem;
          border-radius: 12px;
          font-size: 0.8rem;
          display: flex;
          align-items: center;
          gap: 0.75rem;
          animation: bt-alert-in 0.4s cubic-bezier(0.25,0.46,0.45,0.94) both;
        }
        .bt-alert-danger {
          background: rgba(239,68,68,0.08);
          border: 1px solid rgba(239,68,68,0.15);
          color: #fca5a5;
        }
        .bt-alert-warning {
          background: rgba(251,191,36,0.08);
          border: 1px solid rgba(251,191,36,0.15);
          color: #fde68a;
        }
        @keyframes bt-alert-in {
          from { opacity: 0; transform: translateX(-12px); }
          to { opacity: 1; transform: translateX(0); }
        }

        .bt-category-bar {
          margin-bottom: 0.85rem;
        }
        .bt-category-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.4rem;
        }
        .bt-category-name {
          font-size: 0.8rem;
          font-weight: 500;
          color: rgba(248,250,252,0.7);
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .bt-category-dot {
          width: 8px; height: 8px;
          border-radius: 3px;
        }
        .bt-category-amount {
          font-size: 0.75rem;
          font-weight: 700;
          color: rgba(248,250,252,0.9);
          font-variant-numeric: tabular-nums;
        }
        .bt-bar-track {
          height: 4px;
          background: rgba(255,255,255,0.03);
          border-radius: 99px;
          overflow: hidden;
        }
        .bt-bar-fill {
          height: 100%;
          border-radius: 99px;
          transition: width 0.8s cubic-bezier(0.25,0.46,0.45,0.94);
        }

        .bt-product-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.65rem 0;
          border-bottom: 1px solid rgba(255,255,255,0.03);
          transition: all 0.3s ease;
        }
        .bt-product-row:last-child { border-bottom: none; }
        .bt-product-row:hover {
          background: rgba(255,255,255,0.02);
          border-radius: 8px;
          padding-left: 0.5rem;
          padding-right: 0.5rem;
        }
        .bt-product-info {
          display: flex; align-items: center; gap: 0.75rem;
        }
        .bt-product-icon {
          width: 36px; height: 36px;
          border-radius: 10px;
          display: flex; align-items: center; justify-content: center;
          font-size: 1rem;
          background: rgba(255,255,255,0.03);
          border: 1px solid rgba(255,255,255,0.04);
        }
        .bt-product-name {
          font-size: 0.85rem;
          font-weight: 500;
          color: rgba(248,250,252,0.85);
        }
        .bt-product-cat {
          font-size: 0.7rem;
          color: rgba(148,163,184,0.4);
        }
        .bt-product-price {
          font-size: 0.85rem;
          font-weight: 700;
          color: rgba(248,250,252,0.9);
          font-variant-numeric: tabular-nums;
        }

        .bt-entry-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.6rem 0.75rem;
          border-radius: 10px;
          transition: all 0.3s ease;
          border: 1px solid transparent;
        }
        .bt-entry-row:hover {
          background: rgba(255,255,255,0.02);
          border-color: rgba(255,255,255,0.04);
        }
        .bt-entry-left {
          display: flex; align-items: center; gap: 0.75rem;
        }
        .bt-entry-dot {
          width: 6px; height: 6px;
          border-radius: 50%;
          background: rgba(129,140,248,0.4);
        }
        .bt-entry-name {
          font-size: 0.85rem;
          color: rgba(248,250,252,0.8);
        }
        .bt-entry-cat {
          font-size: 0.7rem;
          color: rgba(148,163,184,0.35);
          margin-left: 0.5rem;
        }
        .bt-entry-right {
          display: flex; align-items: center; gap: 0.75rem;
        }
        .bt-entry-amount {
          font-size: 0.85rem;
          font-weight: 700;
          color: rgba(248,250,252,0.9);
          font-variant-numeric: tabular-nums;
        }

        .bt-check-result {
          margin-top: 1rem;
          padding: 1.25rem;
          border-radius: 14px;
          animation: bt-slide-up 0.4s cubic-bezier(0.25,0.46,0.45,0.94) both;
        }
        .bt-check-ok {
          background: rgba(16,185,129,0.06);
          border: 1px solid rgba(16,185,129,0.12);
        }
        .bt-check-over {
          background: rgba(239,68,68,0.06);
          border: 1px solid rgba(239,68,68,0.12);
        }
        @keyframes bt-slide-up {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .bt-empty {
          text-align: center;
          padding: 3rem 2rem;
          color: rgba(148,163,184,0.3);
          font-size: 0.85rem;
        }

        .bt-limit-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.5rem 0;
          border-bottom: 1px solid rgba(255,255,255,0.03);
          font-size: 0.8rem;
        }
        .bt-limit-row:last-child { border-bottom: none; }
        .bt-limit-info { color: rgba(148,163,184,0.6); }
        .bt-limit-info strong { color: rgba(248,250,252,0.9); font-weight: 700; }

        .bt-loading {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          padding: 3rem;
          color: rgba(148,163,184,0.3);
          font-size: 0.85rem;
        }
        .bt-spinner {
          width: 16px; height: 16px;
          border: 2px solid rgba(129,140,248,0.2);
          border-top-color: rgba(129,140,248,0.6);
          border-radius: 50%;
          animation: bt-spin 0.8s linear infinite;
        }
        @keyframes bt-spin { to { transform: rotate(360deg); } }

        .bt-error {
          padding: 0.75rem 1rem;
          border-radius: 10px;
          background: rgba(239,68,68,0.08);
          border: 1px solid rgba(239,68,68,0.15);
          color: #fca5a5;
          font-size: 0.8rem;
          margin-bottom: 1.5rem;
          animation: bt-alert-in 0.3s ease both;
        }

        .bt-config-bar {
          display: flex;
          gap: 0.75rem;
          align-items: end;
        }
        .bt-config-bar .bt-field { flex: 1; margin-bottom: 0; }

        @media (max-width: 768px) {
          .bt-stat-grid { grid-template-columns: 1fr; }
          .bt-grid-2 { grid-template-columns: 1fr; }
          .bt-hero { padding: 2rem 1.5rem; }
          .bt-config-bar { flex-direction: column; }
        }
      `}</style>

      {/* Hero */}
      <div className="bt-hero" ref={heroRef}>
        <div className="bt-hero-label">Budget Intelligence</div>
        <h1 className="bt-hero-title">BudgetTracker</h1>
        <p className="bt-hero-sub">Real-time spending analytics, intelligent limit enforcement, and predictive budget insights.</p>
      </div>

      {error && <div className="bt-error" role="alert">{error}</div>}

      {/* Config */}
      <div className="bt-glass" style={{ marginBottom: '2rem' }}>
        <div className="bt-section-label">Configuration</div>
        <div className="bt-config-bar">
          <div className="bt-field">
            <label className="bt-label" htmlFor="budget-userid">User ID</label>
            <input id="budget-userid" className="bt-input" value={userId} onChange={e => setUserId(e.target.value)} />
          </div>
          <div className="bt-field">
            <label className="bt-label" htmlFor="budget-period">Period</label>
            <select id="budget-period" className="bt-input" value={period} onChange={e => setPeriod(e.target.value)}>
              {PERIODS.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Stats */}
      {summary && (
        <>
          <div className="bt-stat-grid">
            <div className="bt-stat-card">
              <div className="bt-stat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></svg>
              </div>
              <div className="bt-stat-value">${summary.total_spent.toFixed(2)}</div>
              <div className="bt-stat-label">Total Spent</div>
              <div className="bt-stat-sub">{summary.entry_count} transactions</div>
            </div>
            <div className="bt-stat-card">
              <div className="bt-stat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#43e97b" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12" /></svg>
              </div>
              <div className="bt-stat-value">${summary.daily_average.toFixed(2)}</div>
              <div className="bt-stat-label">Daily Average</div>
              <div className="bt-stat-sub">per day</div>
            </div>
            <div className="bt-stat-card">
              <div className="bt-stat-icon">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fa709a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg>
              </div>
              <div className="bt-stat-value">
                {summary.limits.length > 0 ? `$${summary.limits[0].limit_amount.toFixed(0)}` : '—'}
              </div>
              <div className="bt-stat-label">Budget Limit</div>
              {summary.limits.length > 0 && (
                <div className="bt-stat-sub">${(summary.limits[0].limit_amount - summary.total_spent).toFixed(2)} remaining</div>
              )}
            </div>
          </div>

          {/* Progress Ring */}
          {summary.limits.length > 0 && (
            <div className="bt-glass" style={{ marginBottom: '2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <span className="bt-section-label" style={{ margin: 0 }}>Budget Utilization</span>
                <span style={{ fontSize: '0.85rem', fontWeight: 700, color: spentPct > 90 ? '#f87171' : spentPct > 70 ? '#fbbf24' : '#6ee7b7', fontVariantNumeric: 'tabular-nums' }}>
                  {spentPct.toFixed(1)}%
                </span>
              </div>
              <div className="bt-progress-ring">
                <div className="bt-progress-fill" style={{ width: `${spentPct}%` }} />
              </div>
            </div>
          )}

          {/* Alerts */}
          {summary.alerts.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '2rem' }}>
              {summary.alerts.map((a, i) => (
                <div key={i} className={`bt-alert ${a.startsWith('OVER') ? 'bt-alert-danger' : 'bt-alert-warning'}`}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><line x1="12" y1="9" x2="12" y2="13" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
                  {a}
                </div>
              ))}
            </div>
          )}

          {/* Category Breakdown */}
          {Object.keys(summary.category_breakdown).length > 0 && (
            <div className="bt-glass" style={{ marginBottom: '2rem' }}>
              <div className="bt-section-label">Spending by Category</div>
              {Object.entries(summary.category_breakdown).sort((a, b) => b[1] - a[1]).map(([cat, amount], i) => {
                const pct = summary.total_spent > 0 ? (amount / summary.total_spent) * 100 : 0
                return (
                  <div key={cat} className="bt-category-bar">
                    <div className="bt-category-header">
                      <span className="bt-category-name">
                        <span className="bt-category-dot" style={{ background: GRADIENT_COLORS[i % GRADIENT_COLORS.length] }} />
                        {cat}
                      </span>
                      <span className="bt-category-amount">${amount.toFixed(2)} <span style={{ color: 'rgba(148,163,184,0.35)', fontWeight: 400 }}>({pct.toFixed(0)}%)</span></span>
                    </div>
                    <div className="bt-bar-track">
                      <div className="bt-bar-fill" style={{ width: `${pct}%`, background: GRADIENT_COLORS[i % GRADIENT_COLORS.length] }} />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {/* Set Limit + Check Budget */}
      <div className="bt-grid-2">
        <div className="bt-glass">
          <div className="bt-section-label">Set Budget Limit</div>
          <div className="bt-field">
            <label className="bt-label" htmlFor="limit-period">Period</label>
            <select id="limit-period" className="bt-input" value={limitPeriod} onChange={e => setLimitPeriod(e.target.value)}>
              {PERIODS.map(p => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
            </select>
          </div>
          <div className="bt-field">
            <label className="bt-label" htmlFor="limit-amount">Amount ($)</label>
            <input id="limit-amount" className="bt-input" type="number" min="0" step="0.01" value={limitAmount} onChange={e => setLimitAmount(e.target.value)} placeholder="e.g. 500" />
          </div>
          <div className="bt-field">
            <label className="bt-label" htmlFor="limit-category">Category</label>
            <select id="limit-category" className="bt-input" value={limitCategory} onChange={e => setLimitCategory(e.target.value)}>
              <option value="">All categories</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <button className="bt-btn bt-btn-primary" onClick={handleSetLimit} disabled={!limitAmount || settingLimit}>
            {settingLimit ? (
              <><span className="bt-spinner" style={{ width: 14, height: 14, borderWidth: 1.5 }} /> Setting...</>
            ) : (
              <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg> Set Limit</>
            )}
          </button>
          {limits.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <div className="bt-section-label" style={{ marginBottom: '0.5rem' }}>Active Limits</div>
              {limits.map(l => (
                <div key={l.id} className="bt-limit-row">
                  <span className="bt-limit-info">{l.period} {l.category ? `(${l.category})` : 'all'}: <strong>${l.limit_amount.toFixed(2)}</strong></span>
                  <button className="bt-btn bt-btn-ghost" onClick={() => handleDeleteLimit(l.id)}>Remove</button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bt-glass">
          <div className="bt-section-label">Pre-Purchase Check</div>
          <div className="bt-field">
            <label className="bt-label" htmlFor="check-item">Select Product</label>
            <select id="check-item" className="bt-input" value={checkItem} onChange={e => setCheckItem(e.target.value)}>
              <option value="">Choose a product...</option>
              {SAMPLE_ITEMS.map(p => <option key={p.product_id} value={p.product_id}>{p.icon} {p.product_name} — ${p.amount}</option>)}
            </select>
          </div>
          <button className="bt-btn bt-btn-primary" onClick={handleCheckBudget} disabled={!checkItem || checking}>
            {checking ? (
              <><span className="bt-spinner" style={{ width: 14, height: 14, borderWidth: 1.5 }} /> Analyzing...</>
            ) : (
              <><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg> Check Budget</>
            )}
          </button>
          {checkResult && (
            <div className={`bt-check-result ${checkResult.within_budget ? 'bt-check-ok' : 'bt-check-over'}`}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                {checkResult.within_budget ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" /></svg>
                ) : (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><line x1="15" y1="9" x2="9" y2="15" /><line x1="9" y1="9" x2="15" y2="15" /></svg>
                )}
                <span style={{ fontWeight: 700, fontSize: '0.9rem', color: checkResult.within_budget ? '#6ee7b7' : '#fca5a5' }}>
                  {checkResult.within_budget ? 'Within Budget' : 'Over Budget'}
                </span>
              </div>
              <p style={{ fontSize: '0.8rem', color: 'rgba(148,163,184,0.5)', lineHeight: 1.5 }}>{checkResult.message}</p>
              {checkResult.alerts.length > 0 && (
                <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {checkResult.alerts.map((a, i) => (
                    <p key={i} style={{ fontSize: '0.75rem', color: '#fbbf24' }}>⚠ {a}</p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Quick Track */}
      <div className="bt-glass" style={{ marginBottom: '2rem' }}>
        <div className="bt-section-label">Quick Track</div>
        <div>
          {SAMPLE_ITEMS.map(p => (
            <div key={p.product_id} className="bt-product-row">
              <div className="bt-product-info">
                <div className="bt-product-icon">{p.icon}</div>
                <div>
                  <div className="bt-product-name">{p.product_name}</div>
                  <div className="bt-product-cat">{p.category}</div>
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span className="bt-product-price">${p.amount.toFixed(2)}</span>
                <button className="bt-btn bt-btn-ghost bt-btn-sm" onClick={() => handleTrackEntry(p)}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" /></svg>
                  Track
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Entries */}
      {entries.length > 0 && (
        <div className="bt-glass">
          <div className="bt-section-label">Recent Entries</div>
          <div>
            {entries.slice(0, 15).map(e => (
              <div key={e.id} className="bt-entry-row">
                <div className="bt-entry-left">
                  <span className="bt-entry-dot" />
                  <span className="bt-entry-name">{e.product_name}</span>
                  <span className="bt-entry-cat">{e.category}</span>
                  {e.note && <span className="bt-entry-cat">({e.note})</span>}
                </div>
                <div className="bt-entry-right">
                  <span className="bt-entry-amount">${(e.amount * e.quantity).toFixed(2)}</span>
                  <button className="bt-btn bt-btn-ghost" onClick={() => handleDeleteEntry(e.id)} style={{ padding: '0.2rem 0.5rem', fontSize: '0.65rem' }}>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="bt-loading">
          <span className="bt-spinner" />
          Loading budget data...
        </div>
      )}
    </div>
  )
}
