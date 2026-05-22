import axios from 'axios'
import type { Agent, Product, QueryIntent, UserPreferences, Task } from '../types'

const api = axios.create({ baseURL: 'http://localhost:8000/api' })

export const getAgents = () => api.get<Agent[]>('/agents').then(r => r.data)
export const createAgent = (name: string, task?: string) =>
  api.post<Agent>('/agents', { name, task }).then(r => r.data)
export const getAgent = (id: string) => api.get<Agent>(`/agents/${id}`).then(r => r.data)
export const deleteAgent = (id: string) => api.delete(`/agents/${id}`)
export const runAgent = (id: string) => api.post(`/agents/${id}/run`).then(r => r.data)

export const getProducts = (params?: { category?: string; search?: string; min_price?: number; max_price?: number }) =>
  api.get<Product[]>('/products', { params }).then(r => r.data)

export const getPreferences = () => api.get<UserPreferences>('/preferences').then(r => r.data)
export const updatePreferences = (prefs: UserPreferences) =>
  api.put<UserPreferences>('/preferences', prefs).then(r => r.data)

export const getTasks = () => api.get<Task[]>('/tasks').then(r => r.data)

export const decodeIntent = (query: string) =>
  api.post<{ intent: QueryIntent }>('/intent', { query }).then(r => r.data.intent)

export const WS_URL = 'ws://localhost:8000/ws/agents'
