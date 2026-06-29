import { useEffect, useState } from 'react'
import { catalogSearch, getCatalogCategories } from '../services/api'
import type { CatalogProduct, CatalogSearchResult } from '../types'

export default function CatalogSearch() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [minRating, setMinRating] = useState('')
  const [sortBy, setSortBy] = useState('relevance')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CatalogSearchResult | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [selectedProduct, setSelectedProduct] = useState<CatalogProduct | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getCatalogCategories()
      .then(r => { if (!cancelled) setCategories(r.categories) })
      .catch(() => { if (!cancelled) setError('Failed to load categories') })
    return () => { cancelled = true }
  }, [])

  const search = async (p?: number) => {
    setLoading(true)
    setSelectedProduct(null)
    setError(null)
    try {
      const res = await catalogSearch({
        query: query || undefined,
        category: category || undefined,
        max_price: maxPrice ? parseFloat(maxPrice) : undefined,
        min_rating: minRating ? parseFloat(minRating) : undefined,
        sort_by: sortBy,
        page: p ?? page,
        page_size: 12,
      })
      setResult(res)
      setPage(p ?? page)
    } catch {
      setError('Search failed. Please try again.')
    }
    setLoading(false)
  }

  const stockLabel = (p: CatalogProduct) => {
    if (p.stock === 0) return 'OUT OF STOCK'
    if (p.stock < 10) return `Only ${p.stock} left`
    return 'In Stock'
  }

  const stockColor = (p: CatalogProduct) => {
    if (p.stock === 0) return '#ef5566'
    if (p.stock < 10) return '#f59e0b'
    return '#2bd47c'
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-left">
          <h1 className="page-title">Catalog Search</h1>
          <p className="page-subtitle">Search 906 products across 9 categories</p>
        </div>
      </div>

      {error && <div className="error-banner" role="alert">{error}</div>}

      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div className="form-row">
          <div className="form-group" style={{ flex: 2 }}>
            <label htmlFor="cat-search">Search</label>
            <input id="cat-search" className="input" value={query} onChange={e => setQuery(e.target.value)}
              placeholder="e.g. wireless headphones, running shoes..." aria-label="Search products" />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="cat-category">Category</label>
            <select id="cat-category" className="input" value={category} onChange={e => setCategory(e.target.value)} aria-label="Filter by category">
              <option value="">All Categories</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="cat-maxprice">Max Price</label>
            <input id="cat-maxprice" className="input" type="number" min="0" value={maxPrice}
              onChange={e => setMaxPrice(e.target.value)} placeholder="e.g. 100" aria-label="Maximum price" />
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="cat-rating">Min Rating</label>
            <select id="cat-rating" className="input" value={minRating} onChange={e => setMinRating(e.target.value)} aria-label="Minimum rating">
              <option value="">Any</option>
              <option value="3">3+</option>
              <option value="3.5">3.5+</option>
              <option value="4">4+</option>
              <option value="4.5">4.5+</option>
            </select>
          </div>
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="cat-sort">Sort By</label>
            <select id="cat-sort" className="input" value={sortBy} onChange={e => setSortBy(e.target.value)} aria-label="Sort results by">
              <option value="relevance">Relevance</option>
              <option value="price_asc">Price: Low-High</option>
              <option value="price_desc">Price: High-Low</option>
              <option value="rating">Rating</option>
              <option value="name">Name</option>
            </select>
          </div>
          <button className="btn btn-primary" onClick={() => search(1)}
            disabled={loading} style={{ height: 36, alignSelf: 'flex-end' }} aria-label="Search">
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '1.5rem' }}>
        <div style={{ flex: selectedProduct ? 1.5 : 1 }}>
          {result && (
            <p style={{ color: '#a0aec0', fontSize: '0.85rem', marginBottom: '0.75rem' }} role="status">
              {result.total} product{result.total !== 1 ? 's' : ''} found
              {result.query && <> for "<strong>{result.query}</strong>"</>}
            </p>
          )}

          {loading ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }} role="status">
              <p style={{ color: 'var(--text-dim)' }}>Searching catalog...</p>
            </div>
          ) : (
            <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))' }}>
              {result?.products.map(p => (
                <div key={p.id} className="card animate-in" style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedProduct(selectedProduct?.id === p.id ? null : p)}
                  role="button" tabIndex={0} aria-label={`${p.name}, $${p.price.toFixed(2)}`}
                  onKeyDown={e => e.key === 'Enter' && setSelectedProduct(selectedProduct?.id === p.id ? null : p)}>
                  <div className="card-header">
                    <h4 style={{ fontSize: '0.9rem' }}>{p.name}</h4>
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#a0aec0', marginBottom: '0.25rem' }}>
                    {p.category}
                  </div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.25rem' }}>
                    ${p.price.toFixed(2)}
                  </div>
                  <div style={{ fontSize: '0.85rem' }}>
                    <span style={{ color: '#f59e0b' }} aria-label={`${p.rating} out of 5 stars`}>
                      <span aria-hidden="true">{'★'.repeat(Math.round(p.rating))}{'☆'.repeat(5 - Math.round(p.rating))}</span>
                    </span>
                    <span style={{ color: '#6b7280', marginLeft: 4 }}>{p.rating}/5</span>
                  </div>
                  <div style={{ fontSize: '0.8rem', marginTop: '0.25rem', color: stockColor(p) }}>
                    {stockLabel(p)}
                  </div>
                </div>
              ))}
              {result && result.products.length === 0 && (
                <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                  <div className="empty-icon" aria-hidden="true">✦</div>
                  <p>No products found. Try adjusting your filters.</p>
                </div>
              )}
            </div>
          )}

          {result && result.total_pages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1.5rem' }}>
              <button className="btn" disabled={page <= 1} onClick={() => search(page - 1)}
                style={{ height: 32, fontSize: '0.85rem' }} aria-label="Previous page">← Prev</button>
              <span style={{ color: '#a0aec0', alignSelf: 'center', fontSize: '0.85rem' }}>
                Page {page} of {result.total_pages}
              </span>
              <button className="btn" disabled={page >= result.total_pages} onClick={() => search(page + 1)}
                style={{ height: 32, fontSize: '0.85rem' }} aria-label="Next page">Next →</button>
            </div>
          )}
        </div>

        {selectedProduct && (
          <div className="card animate-in" style={{ flex: 1, height: 'fit-content', position: 'sticky', top: '1rem' }} role="complementary" aria-label="Product details">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <p className="section-title" style={{ margin: 0 }}>Product Details</p>
              <button className="btn" onClick={() => setSelectedProduct(null)}
                style={{ height: 28, width: 28, padding: 0, fontSize: '0.85rem' }} aria-label="Close product details">✕</button>
            </div>
            <h2 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>{selectedProduct.name}</h2>
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
              <span className="tag" style={{ background: '#1a3a2a', color: '#2bd47c', padding: '4px 10px', borderRadius: 6, fontSize: '0.8rem' }}>
                {selectedProduct.category}
              </span>
              <span style={{ fontSize: '1.3rem', fontWeight: 700 }}>${selectedProduct.price.toFixed(2)}</span>
              <span style={{ color: '#f59e0b', fontSize: '0.9rem' }}>
                <span aria-hidden="true">{'★'.repeat(Math.round(selectedProduct.rating))}{'☆'.repeat(5 - Math.round(selectedProduct.rating))}</span>
                <span style={{ color: '#6b7280', marginLeft: 4 }}>{selectedProduct.rating}/5</span>
              </span>
            </div>
            <p style={{ color: '#a0aec0', fontSize: '0.9rem', marginBottom: '0.75rem' }}>
              {selectedProduct.description}
            </p>
            <div style={{ fontSize: '0.85rem', color: stockColor(selectedProduct) }}>
              {stockLabel(selectedProduct)} · ID: #{selectedProduct.id}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
