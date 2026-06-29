import { useEffect, useState, useRef } from 'react'
import { getPreferences, updatePreferences } from '../services/api'
import type { UserPreferences } from '../types'

const allCategories = ['Electronics', 'Sports', 'Home', 'Fashion']

export default function Preferences() {
  const [prefs, setPrefs] = useState<UserPreferences>({
    categories: [],
    price_min: 0,
    price_max: 10000,
    brands: [],
    budget: 1000,
  })
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    getPreferences()
      .then(data => { if (!cancelled) setPrefs(data) })
      .catch(() => { if (!cancelled) setError('Failed to load preferences') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  const toggleCategory = (cat: string) => {
    setPrefs(p => ({
      ...p,
      categories: p.categories.includes(cat)
        ? p.categories.filter(c => c !== cat)
        : [...p.categories, cat],
    }))
  }

  const handleSave = async () => {
    setError(null)
    try {
      await updatePreferences(prefs)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch { setError('Failed to save preferences') }
  }

  if (loading) {
    return (
      <div>
        <div className="page-header">
          <div className="page-header-left">
            <h1 className="page-title">Shopping Preferences</h1>
            <p className="page-subtitle">Customize your shopping experience</p>
          </div>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }} role="status">
          <p style={{ color: 'var(--text-dim)' }}>Loading preferences...</p>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Shopping Preferences</h1>
          <p className="page-subtitle">Customize your shopping experience</p>
        </div>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <div className="prefs-panel">
        <fieldset>
          <legend>Preferred Categories</legend>
          <div className="checkbox-grid">
            {allCategories.map(cat => (
              <label key={cat}>
                <input
                  type="checkbox"
                  checked={prefs.categories.includes(cat)}
                  onChange={() => toggleCategory(cat)}
                  aria-label={`Category: ${cat}`}
                />
                {cat}
              </label>
            ))}
          </div>
        </fieldset>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label htmlFor="pref-min-price">Min Price ($)</label>
            <input
              id="pref-min-price"
              className="input"
              type="number"
              value={prefs.price_min}
              onChange={e => setPrefs(p => ({ ...p, price_min: +e.target.value }))}
              aria-label="Minimum price"
            />
          </div>
          <div className="form-group">
            <label htmlFor="pref-max-price">Max Price ($)</label>
            <input
              id="pref-max-price"
              className="input"
              type="number"
              value={prefs.price_max}
              onChange={e => setPrefs(p => ({ ...p, price_max: +e.target.value }))}
              aria-label="Maximum price"
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="pref-budget">Budget ($)</label>
          <input
            id="pref-budget"
            className="input"
            type="number"
            value={prefs.budget}
            onChange={e => setPrefs(p => ({ ...p, budget: +e.target.value }))}
            aria-label="Budget"
          />
        </div>

        <div className="form-group">
          <label htmlFor="pref-brands">Preferred Brands</label>
          <input
            id="pref-brands"
            className="input"
            value={prefs.brands.join(', ')}
            onChange={e => setPrefs(p => ({ ...p, brands: e.target.value.split(',').map(b => b.trim()).filter(Boolean) }))}
            placeholder="e.g. Nike, Apple, Samsung"
            aria-label="Preferred brands (comma separated)"
          />
        </div>

        <button className="btn btn-primary" onClick={handleSave} aria-label="Save preferences">
          {saved ? 'Saved' : 'Save Preferences'}
        </button>
      </div>

      {saved && <div className="toast" role="status">Preferences saved successfully</div>}
    </div>
  )
}
