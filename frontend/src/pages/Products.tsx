import { useEffect, useState } from 'react'
import { getProducts } from '../services/api'
import ProductCard from '../components/ProductCard'
import type { Product } from '../types'

const categories = ['', 'Electronics', 'Sports', 'Home', 'Fashion']

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true); setError(null)
    getProducts({ category: category || undefined, search: search || undefined })
      .then(data => { if (!cancelled) setProducts(data) })
      .catch(() => { if (!cancelled) setError('Failed to load products') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [category, search])

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Products</h1>
          <p className="page-subtitle">Browse and search available products</p>
        </div>
      </div>

      <div className="filters-bar">
        <div className="form-group" style={{ flex: 1, minWidth: 200 }}>
          <label htmlFor="product-search">Search</label>
          <input id="product-search" className="input" value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search products..." />
        </div>
        <div className="form-group" style={{ minWidth: 160 }}>
          <label htmlFor="product-category">Category</label>
          <select id="product-category" className="input" value={category} onChange={e => setCategory(e.target.value)}>
            {categories.map(c => <option key={c} value={c}>{c || 'All Categories'}</option>)}
          </select>
        </div>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      {loading ? (
        <div className="grid">
          {[1,2,3,4,5,6].map(i => <div key={i} className="skeleton-card" aria-hidden="true" />)}
        </div>
      ) : (
        <div className="grid" role="list" aria-label="Product grid">
          {products.map(p => <ProductCard key={p.id} product={p} />)}
        </div>
      )}
      {!loading && products.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-icon" aria-hidden="true">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.3"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
          </div>
          <p>No products found matching your filters.</p>
        </div>
      )}
    </div>
  )
}
