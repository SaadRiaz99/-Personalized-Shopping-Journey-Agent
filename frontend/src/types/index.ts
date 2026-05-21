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
