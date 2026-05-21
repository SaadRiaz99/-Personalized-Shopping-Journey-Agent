import type { Product } from '../types'

interface Props {
  product: Product
}

export default function ProductCard({ product }: Props) {
  return (
    <div className="card">
      <div className="card-header">
        <h3>{product.name}</h3>
        <span className="price">${product.price.toFixed(2)}</span>
      </div>
      <p className="description">{product.description}</p>
      <div className="meta">
        <span className="meta-item">📁 {product.category}</span>
        <span className="meta-item rating">★ {product.rating.toFixed(1)}</span>
      </div>
      <div className="tags">
        {product.tags.map(t => <span key={t} className="tag">{t}</span>)}
      </div>
    </div>
  )
}
