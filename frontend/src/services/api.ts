import axios from 'axios'
import type { Agent, Product, QueryIntent, UserPreferences, Task, CatalogSearchResult, CatalogProduct, Promotion, DealSessionRequest, DealResult, PriceMatchProduct, PriceCheckResponse, PriceHistoryPoint, PriceDropAlert, DiscountResult, GiftRecipient, GiftFinderResult, CrossSellResult, WishlistItem, PriceAlertEvent, LoginRequest, RegisterRequest, TokenResponse, LoginHistoryEntry, UserSession, AuthUser } from '../types'

const api = axios.create({ baseURL: 'http://localhost:8000/api' })

// Auth interceptor: attach access token and handle refresh
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  response => response,
  async error => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('http://localhost:8000/api/auth/refresh', {
            refresh_token: refreshToken,
          })
          const data = res.data as TokenResponse
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch { /* refresh failed */ }
      }
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

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

export const getRecommendations = () =>
  api.get<Product[]>('/recommendations').then(r => r.data)

export const findGifts = (recipient: GiftRecipient) =>
  api.post<GiftFinderResult>('/gift-finder/find', recipient).then(r => r.data)

export const getCrossSell = (productId: number, cartIds?: number[]) =>
  api.get<CrossSellResult>(`/cross-sell/${productId}`, {
    params: cartIds?.length ? { cart_ids: cartIds.join(',') } : undefined,
  }).then(r => r.data)

export const getCrossSellBatch = (productIds: number[], cartIds?: number[]) =>
  api.post<{ results: Record<string, CrossSellResult> }>('/cross-sell/batch', {
    product_ids: productIds, cart_ids: cartIds,
  }).then(r => r.data)

export const getWishlist = (userId?: string) =>
  api.get<{ items: WishlistItem[]; total: number }>('/wishlist', {
    headers: userId ? { 'x-user-id': userId } : undefined,
  }).then(r => r.data)

export const addToWishlist = (item: Partial<WishlistItem>, userId?: string) =>
  api.post<WishlistItem>('/wishlist', item, {
    headers: userId ? { 'x-user-id': userId } : undefined,
  }).then(r => r.data)

export const removeFromWishlist = (itemId: string) =>
  api.delete(`/wishlist/${itemId}`).then(r => r.data)

export const updateWishlistItem = (itemId: string, body: Partial<WishlistItem>) =>
  api.patch<WishlistItem>(`/wishlist/${itemId}`, body).then(r => r.data)

// ── Advanced Auth ──────────────────────────────────────────

export const authLogin = (body: LoginRequest) =>
  api.post<TokenResponse>('/auth/login', body).then(r => r.data)

export const authRegister = (body: RegisterRequest) =>
  api.post<{ message: string; user_id: string; username: string }>('/auth/register', body).then(r => r.data)

export const authRefresh = (refreshToken: string) =>
  api.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken }).then(r => r.data)

export const authLogout = () =>
  api.post<{ message: string }>('/auth/logout').then(r => r.data)

export const authMe = () =>
  api.get<AuthUser>('/auth/me').then(r => r.data)

export const authChangePassword = (currentPassword: string, newPassword: string) =>
  api.post<{ message: string }>('/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  }).then(r => r.data)

export const authVerifyEmail = () =>
  api.post<{ message: string }>('/auth/verify-email/confirm').then(r => r.data)

export const authEnable2FA = () =>
  api.post<{ message: string; secret: string; demo_code: string }>('/auth/2fa/enable').then(r => r.data)

export const authDisable2FA = () =>
  api.post<{ message: string }>('/auth/2fa/disable').then(r => r.data)

export const authVerify2FA = (code: string) =>
  api.post<{ message: string; valid: boolean }>('/auth/2fa/verify', { code }).then(r => r.data)

export const authGetHistory = () =>
  api.get<{ entries: LoginHistoryEntry[]; total: number }>('/auth/history').then(r => r.data)

export const authGetSessions = () =>
  api.get<{ sessions: UserSession[]; total: number }>('/auth/sessions').then(r => r.data)

export const authRevokeSession = (sessionId: string) =>
  api.delete(`/auth/sessions/${sessionId}`).then(r => r.data)

export const authListUsers = () =>
  api.get<{ users: AuthUser[]; total: number }>('/auth/users').then(r => r.data)

export const checkPriceAlerts = (userId?: string) =>
  api.post<{ alerts_triggered: PriceAlertEvent[]; count: number }>('/wishlist/alerts/check', {}, {
    headers: userId ? { 'x-user-id': userId } : undefined,
  }).then(r => r.data)

export const getPriceAlertsHistory = (userId?: string) =>
  api.get<{ alerts: PriceAlertEvent[]; total: number }>('/wishlist/alerts', {
    headers: userId ? { 'x-user-id': userId } : undefined,
  }).then(r => r.data)

export const WS_URL = 'ws://192.168.0.34:8000/ws/agents'
