export interface QueryIntent {
  category: string | null
  budget: number | null
  budget_currency: string
  occasion: string | null
  style_preferences: string[]
  urgency: string | null
  raw_query: string
}

export interface Agent {
  id: string
  name: string
  status: 'idle' | 'running' | 'completed' | 'error'
  task: string | null
  created_at: string
  updated_at: string
}

export interface Product {
  id: string
  name: string
  description: string
  price: number
  category: string
  image_url: string | null
  rating: number
  tags: string[]
}

export interface UserPreferences {
  categories: string[]
  price_min: number
  price_max: number
  brands: string[]
  budget: number
}

export interface Task {
  id: string
  agent_id: string
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  result: string | null
  created_at: string
  updated_at: string
}

export interface WSEvent {
  event: string
  data: Record<string, unknown>
}

export interface CartItem {
  product_id: string
  sku: string
  name: string
  price: number
  quantity: number
  category: string
}

export interface DealSessionRequest {
  user_id: string
  items: CartItem[]
  loyalty_tier: 'bronze' | 'silver' | 'gold' | 'platinum'
  budget?: number
  opted_out?: boolean
}

export interface AppliedDiscount {
  promotion_id: string
  promotion_name: string
  discount_type: string
  discount_amount: number
  description: string
}

export interface DealResult {
  user_id: string
  message: string
  subtotal: number
  final_total: number
  total_savings: number
  applied_discounts: AppliedDiscount[]
  savings_breakdown: string
}

export interface Promotion {
  id: string
  name: string
  description: string
  type: string
  value: number
  stackable: boolean
  min_purchase: number | null
  max_discount: number | null
  applicable_categories: string[]
  min_loyalty_tier: string
  requires_opt_in: boolean
  active: boolean
}

export interface CatalogProduct {
  id: number
  name: string
  category: string
  price: number
  rating: number
  stock: number
  description: string
}

export interface CatalogSearchResult {
  total: number
  page: number
  page_size: number
  total_pages: number
  products: CatalogProduct[]
  query: string
  category: string | null
}

export interface CompetitorPrice {
  sku: string
  store: string
  price: number
  all_prices: Record<string, number>
}

export interface PriceHistoryPoint {
  date: string
  price: number
}

export interface PriceDropAlert {
  date: string
  from: number
  to: number
  drop_pct: number
}

export interface PriceMatchProduct {
  id: string
  name: string
  category: string
  store_price: number
  rating: number
  sku: string
  tags: string[]
  description: string
  competitor: CompetitorPrice | null
  history: PriceHistoryPoint[]
  alerts: PriceDropAlert[]
}

export interface DiscountResult {
  id: string
  agent_id: string
  product_id: string
  sku: string
  store_price: number
  competitor_store: string
  competitor_price: number
  discount_amount: number
  new_price: number
  status: 'pending' | 'approved' | 'applied' | 'declined'
  created_at: string
}

export interface PriceCheckResponse {
  agent: Agent
  discount: DiscountResult
  guardrail?: {
    input: { allowed: boolean; reason: string; category: string | null }
    rate: { allowed: boolean; reason: string; category: string | null }
  }
}
