import { useEffect, useState } from 'react'
import { getProducts } from '../services/api'
import ProductCard from '../components/ProductCard'
import type { Product } from '../types'

const categories = ['', 'Electronics', 'Sports', 'Home', 'Fashion']

export default function Products() {
  const [products, setProducts] = useState<Product[]>([])
  const [category, setCategory] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    getProducts({ category: category || undefined, search: search || undefined }).then(setProducts)
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
          <label>Search</label>
          <input
            className="input"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search products..."
          />
        </div>
        <div className="form-group" style={{ minWidth: 160 }}>
          <label>Category</label>
          <select className="input" value={category} onChange={e => setCategory(e.target.value)}>
            {categories.map(c => (
              <option key={c} value={c}>{c || 'All Categories'}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid">
        {products.map(p => <ProductCard key={p.id} product={p} />)}
      </div>
      {products.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">✦</div>
          <p>No products found matching your filters.</p>
        </div>
      )}
    </div>
  )
}
