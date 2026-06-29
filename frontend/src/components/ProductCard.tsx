import type { Product } from '../types'

interface Props {
  product: Product
}

export default function ProductCard({ product }: Props) {
  return (
    <div className="card" role="article" aria-label={`${product.name}, $${product.price.toFixed(2)}`}>
      <div className="card-header">
        <h3>{product.name}</h3>
        <span className="price" aria-label={`Price: $${product.price.toFixed(2)}`}>${product.price.toFixed(2)}</span>
      </div>
      <p className="description">{product.description}</p>
      <div className="meta">
        <span className="meta-item" aria-label={`Category: ${product.category}`}>{product.category}</span>
        <span className="meta-item rating" aria-label={`Rating: ${product.rating.toFixed(1)} out of 5`}>
          <span aria-hidden="true">★</span> {product.rating.toFixed(1)}
        </span>
      </div>
      <div className="tags" aria-label="Product tags">
        {product.tags.map(t => <span key={t} className="tag">{t}</span>)}
      </div>
    </div>
  )
}
