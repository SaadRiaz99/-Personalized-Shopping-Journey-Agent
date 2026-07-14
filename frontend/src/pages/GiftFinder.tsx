import { useState } from 'react'
import { motion } from 'framer-motion'
import { findGifts, addToWishlist } from '../services/api'
import type { GiftRecipient, GiftFinderResult, GiftRecommendation } from '../types'

const OCCASIONS = ['Birthday', 'Anniversary', 'Wedding', 'Christmas', 'Graduation', "Valentine's Day", "Mother's Day", "Father's Day", 'Housewarming', 'Just Because']
const RELATIONSHIPS = ['Spouse', 'Parent', 'Sibling', 'Friend', 'Child', 'Partner', 'Coworker', 'Grandparent', 'Other']
const AGE_GROUPS = ['Infant', 'Toddler', 'Child', 'Teen', 'Young Adult', 'Adult', 'Senior']

export default function GiftFinder() {
  const [occasion, setOccasion] = useState('')
  const [relationship, setRelationship] = useState('')
  const [ageGroup, setAgeGroup] = useState('')
  const [interests, setInterests] = useState('')
  const [budget, setBudget] = useState('')
  const [gender, setGender] = useState('')
  const [result, setResult] = useState<GiftFinderResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFind = async () => {
    setLoading(true); setResult(null); setError(null)
    try {
      const recipient: GiftRecipient = {
        occasion: occasion || 'Just Because', relationship: relationship || 'Friend',
        age_group: ageGroup || 'Adult',
        interests: interests.split(',').map(s => s.trim()).filter(Boolean),
        budget: budget ? parseFloat(budget) : undefined,
        gender_preference: gender || undefined,
      }
      setResult(await findGifts(recipient))
    } catch { setError('Failed to find gifts.'); setResult(null) }
    setLoading(false)
  }

  const handleSaveToWishlist = async (rec: GiftRecommendation) => {
    const p = rec.product as Record<string, unknown>
    try {
      await addToWishlist({
        product_id: p.id as number, product_name: p.name as string, product_price: p.price as number,
        product_category: p.category as string, product_image: (p.image_url as string) || null,
        note: `Gift idea \u2014 ${result?.recipient.occasion} for ${result?.recipient.relationship}`,
      })
    } catch { setError('Failed to save to wishlist.') }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <motion.h1 initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="page-title">Gift Finder</motion.h1>
          <p className="page-subtitle">Find the perfect gift for any occasion</p>
        </div>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <p className="section-title" style={{ marginBottom: '0.75rem' }}>Tell us about the recipient</p>
        <div className="form-row">
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="gift-occasion">Occasion</label>
            <select id="gift-occasion" className="input" value={occasion} onChange={e => setOccasion(e.target.value)}>
              <option value="">Select occasion...</option>
              {OCCASIONS.map(o => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="gift-relationship">Relationship</label>
            <select id="gift-relationship" className="input" value={relationship} onChange={e => setRelationship(e.target.value)}>
              <option value="">Select relationship...</option>
              {RELATIONSHIPS.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="gift-age">Age Group</label>
            <select id="gift-age" className="input" value={ageGroup} onChange={e => setAgeGroup(e.target.value)}>
              <option value="">Select age group...</option>
              {AGE_GROUPS.map(a => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
        </div>
        <div className="form-row" style={{ marginTop: '0.5rem' }}>
          <div className="form-group" style={{ flex: 2 }}>
            <label htmlFor="gift-interests">Interests (comma-separated)</label>
            <input id="gift-interests" className="input" value={interests} onChange={e => setInterests(e.target.value)}
              placeholder="e.g. music, cooking, hiking, gaming" />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="gift-budget">Budget ($)</label>
            <input id="gift-budget" className="input" type="number" min="0" step="1" value={budget}
              onChange={e => setBudget(e.target.value)} placeholder="e.g. 50" />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="gift-gender">Gender Preference</label>
            <select id="gift-gender" className="input" value={gender} onChange={e => setGender(e.target.value)}>
              <option value="">Prefer not to say</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
            </select>
          </div>
        </div>
        <button className="btn btn-primary" onClick={handleFind} disabled={loading}
          style={{ marginTop: '0.75rem', width: '100%', height: 42 }}>
          {loading ? <span style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: 'center' }}><span className="spinner" /> Finding Gifts...</span> : 'Find Perfect Gifts'}
        </button>
      </div>

      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '2.5rem' }} role="status">
          <span className="spinner" style={{ margin: '0 auto', display: 'block' }} />
          <p style={{ color: 'var(--text-dim)', marginTop: '0.75rem' }}>Searching for gift ideas...</p>
        </div>
      )}

      {result && (
        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="card" style={{ marginBottom: '1.5rem', borderLeft: '3px solid var(--primary)' }}>
          <p className="section-title" style={{ marginBottom: '0.25rem' }}>Gift Agent Report</p>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{result.summary}</p>
          {result.total_found === 0 && (
            <div className="empty-state" style={{ padding: '1.5rem' }}>
              <p>Try adjusting the criteria.</p>
            </div>
          )}
        </motion.div>
      )}

      {result && result.recommendations.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
            <span className="status-pill" style={{ background: 'var(--primary-glow)', color: 'var(--primary)', border: '1px solid rgba(129,140,248,0.15)' }}>
              {result.total_found} gift ideas
            </span>
            <span className="status-pill" style={{ background: 'var(--success-glow)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.15)' }}>
              Sorted by relevance
            </span>
          </div>
          {result.recommendations.map((rec, i) => {
            const p = rec.product as Record<string, unknown>
            return (
              <motion.div key={i} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                className="card animate-in" style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', padding: '1rem 1.25rem' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem', flexWrap: 'wrap' }}>
                    <h3 style={{ margin: 0, fontSize: '0.95rem' }}>{p.name as string}</h3>
                    <span className="tag" style={{ background: 'var(--primary-glow)', color: 'var(--primary)' }}>${(p.price as number).toFixed(2)}</span>
                    <span className="tag">{p.category as string}</span>
                  </div>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', margin: '0.25rem 0' }}>
                    {(p.description as string)?.slice(0, 120)}
                  </p>
                  <div style={{ display: 'flex', gap: '0.3rem', flexWrap: 'wrap', marginTop: '0.35rem' }}>
                    {rec.match_reasons.slice(0, 3).map((reason, ri) => (
                      <span key={ri} className="tag" style={{ background: 'var(--primary-subtle)', color: 'var(--primary)', border: '1px solid rgba(129,140,248,0.1)', fontSize: '0.72rem' }}>{reason}</span>
                    ))}
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.35rem', flexShrink: 0 }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontWeight: 700 }}>{(rec.relevance_score * 100).toFixed(0)}%</span>
                  <button className="btn btn-ghost" onClick={() => handleSaveToWishlist(rec)} style={{ height: 28, fontSize: '0.72rem', padding: '0 10px' }}>Save</button>
                </div>
              </motion.div>
            )
          })}
        </div>
      )}
    </div>
  )
}
