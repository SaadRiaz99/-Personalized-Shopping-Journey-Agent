import axios from 'axios'
import type { Agent, Product, QueryIntent, UserPreferences, Task, CatalogSearchResult, CatalogProduct, Promotion, DealSessionRequest, DealResult, PriceMatchProduct, PriceCheckResponse, PriceHistoryPoint, PriceDropAlert, DiscountResult } from '../types'

const api = axios.create({ baseURL: 'http://localhost:8000/api' })

export const getAgents = () => api.get<Agent[]>('/agents').then(r => r.data)
export const createAgent = (name: string, task?: string) =>
  api.post<Agent>('/agents', { name, task }).then(r => r.data)
export const getAgent = (id: string) => api.get<Agent>(`/agents/${id}`).then(r => r.data)
export const deleteAgent = (id: string) => api.delete(`/agents/${id}`)
export const runAgent = (id: string) => api.post(`/agents/${id}/run`).then(r => r.data)
export const runCollaboration = (query: string) => api.post('/agents/collaboration', { query }).then(r => r.data)

export const getProducts = (params?: { category?: string; search?: string; min_price?: number; max_price?: number }) =>
  api.get<Product[]>('/products', { params }).then(r => r.data)

export const getPreferences = () => api.get<UserPreferences>('/preferences').then(r => r.data)
export const updatePreferences = (prefs: UserPreferences) =>
  api.put<UserPreferences>('/preferences', prefs).then(r => r.data)

export const getTasks = () => api.get<Task[]>('/tasks').then(r => r.data)

export const decodeIntent = (query: string) =>
  api.post<{ intent: QueryIntent }>('/intent', { query }).then(r => r.data.intent)

export const catalogSearch = (params: {
  query?: string; category?: string; max_price?: number; min_price?: number;
  min_rating?: number; sort_by?: string; page?: number; page_size?: number
}) =>
  api.get<CatalogSearchResult>('/catalog/search', { params }).then(r => r.data)

export const getCatalogProduct = (id: number) =>
  api.get<CatalogProduct>(`/catalog/products/${id}`).then(r => r.data)

export const getCatalogCategories = () =>
  api.get<{ categories: string[]; total: number }>('/catalog/categories').then(r => r.data)

export const getPromotions = () =>
  api.get<Promotion[]>('/deals/promotions').then(r => r.data)

export const optimizeCart = (body: DealSessionRequest) =>
  api.post<DealResult>('/deals/optimize', body).then(r => r.data)

export const applyDealStack = (stackId: string) =>
  api.post(`/deals/apply/${stackId}`).then(r => r.data)

export const getPriceMatchProducts = () =>
  api.get<PriceMatchProduct[]>('/price-match/products').then(r => r.data)

export const checkPriceMatch = (productId: string, sku: string, currentPrice: number, userId?: string) =>
  api.post<PriceCheckResponse>('/price-match/check', { product_id: productId, sku, current_price: currentPrice },
    userId ? { headers: { 'x-user-id': userId } } : undefined
  ).then(r => r.data)

export const getPriceHistory = (sku: string) =>
  api.get<{ sku: string; history: PriceHistoryPoint[]; alerts: PriceDropAlert[] }>(`/price-match/history/${sku}`).then(r => r.data)

export const getPriceAlerts = (threshold?: number) =>
  api.get<{ product_id: string; product_name: string; sku: string; alerts: PriceDropAlert[] }[]>('/price-match/alerts', { params: { threshold } }).then(r => r.data)

export const listDiscounts = () =>
  api.get<DiscountResult[]>('/price-match/discounts').then(r => r.data)

export const applyDiscount = (discountId: string) =>
  api.post<DiscountResult>(`/price-match/discounts/${discountId}/apply`).then(r => r.data)

export const WS_URL = 'ws://192.168.0.34:8000/ws/agents'
