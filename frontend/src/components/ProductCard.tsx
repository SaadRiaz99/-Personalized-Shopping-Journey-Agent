import type { Product } from '../types'

interface Props {
  product: Product
}

const CATEGORY_COLORS: Record<string, string> = {
  Electronics: '#818cf8',
  Sports: '#10b981',
  Home: '#f59e0b',
  Fashion: '#f43f5e',
}

export default function ProductCard({ product }: Props) {
  const catColor = CATEGORY_COLORS[product.category] || '#818cf8'

  return (
    <div className="card" role="article" aria-label={`${product.name}, $${product.price.toFixed(2)}`}
      style={{ cursor: 'default' }}>
      <div style={{
        height: 4,
        borderRadius: '4px 4px 0 0',
        background: `linear-gradient(90deg, ${catColor}, transparent)`,
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        opacity: 0.6,
      }} />
      <div className="card-header">
        <h3 style={{ flex: 1, fontSize: '0.95rem' }}>{product.name}</h3>
        <span className="price" aria-label={`Price: $${product.price.toFixed(2)}`}>${product.price.toFixed(2)}</span>
      </div>
      <p className="description" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
        {product.description}
      </p>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div className="meta">
          <span className="meta-item" style={{ color: catColor, fontWeight: 600, fontSize: '0.75rem' }}>
            {product.category}
          </span>
          <span className="meta-item rating" aria-label={`Rating: ${product.rating.toFixed(1)} out of 5`}>
            <span aria-hidden="true">&#9733;</span> {product.rating.toFixed(1)}
          </span>
        </div>
      </div>
      {product.tags.length > 0 && (
        <div className="tags" aria-label="Product tags">
          {product.tags.slice(0, 4).map(t => <span key={t} className="tag">{t}</span>)}
        </div>
      )}
    </div>
  )
}
