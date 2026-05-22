import { useEffect, useState } from 'react'
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

  useEffect(() => {
    getPreferences().then(setPrefs)
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
    await updatePreferences(prefs)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Shopping Preferences</h1>
          <p className="page-subtitle">Customize your shopping experience</p>
        </div>
      </div>

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
                />
                {cat}
              </label>
            ))}
          </div>
        </fieldset>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label>Min Price ($)</label>
            <input
              className="input"
              type="number"
              value={prefs.price_min}
              onChange={e => setPrefs(p => ({ ...p, price_min: +e.target.value }))}
            />
          </div>
          <div className="form-group">
            <label>Max Price ($)</label>
            <input
              className="input"
              type="number"
              value={prefs.price_max}
              onChange={e => setPrefs(p => ({ ...p, price_max: +e.target.value }))}
            />
          </div>
        </div>

        <div className="form-group">
          <label>Budget ($)</label>
          <input
            className="input"
            type="number"
            value={prefs.budget}
            onChange={e => setPrefs(p => ({ ...p, budget: +e.target.value }))}
          />
        </div>

        <div className="form-group">
          <label>Preferred Brands</label>
          <input
            className="input"
            value={prefs.brands.join(', ')}
            onChange={e => setPrefs(p => ({ ...p, brands: e.target.value.split(',').map(b => b.trim()).filter(Boolean) }))}
            placeholder="e.g. Nike, Apple, Samsung"
          />
        </div>

        <button className="btn btn-primary" onClick={handleSave}>
          {saved ? '✓ Saved' : 'Save Preferences'}
        </button>
      </div>

      {saved && <div className="toast">✓ Preferences saved successfully</div>}
    </div>
  )
}
