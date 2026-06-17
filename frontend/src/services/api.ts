import axios from 'axios'
import type { Document, Conversation, Message, ChatRequest, ChatResponse, AdminStats, TokenResponse, LoginRequest, RegisterRequest, LoginHistoryEntry, UserSession, AuthUser } from '../types'

const api = axios.create({ baseURL: 'http://localhost:8000/api' })

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

export const getDocuments = () =>
  api.get<{ documents: Document[]; total: number }>('/documents').then(r => r.data)

export const uploadDocument = (file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<{ message: string; document: Document }>('/documents/upload', form).then(r => r.data)
}

export const deleteDocument = (id: string) =>
  api.delete<{ message: string }>(`/documents/${id}`).then(r => r.data)

export const sendChat = (body: ChatRequest) =>
  api.post<ChatResponse>('/chat/send', body).then(r => r.data)

export const getConversations = () =>
  api.get<{ conversations: Conversation[]; total: number }>('/conversations').then(r => r.data)

export const createConversation = (title: string, documentIds: string[] = []) =>
  api.post<{ conversation: Conversation }>('/conversations', { title, document_ids: documentIds }).then(r => r.data)

export const getConversation = (id: string) =>
  api.get<{ conversation: Conversation; messages: Message[] }>(`/conversations/${id}`).then(r => r.data)

export const deleteConversation = (id: string) =>
  api.delete<{ message: string }>(`/conversations/${id}`).then(r => r.data)

export const getConversationMessages = (id: string) =>
  api.get<{ messages: Message[]; total: number }>(`/chat/${id}/messages`).then(r => r.data)

export const getAdminStats = () =>
  api.get<AdminStats>('/admin/stats').then(r => r.data)

export const getAdminUsers = () =>
  api.get<{ users: AuthUser[]; total: number }>('/admin/users').then(r => r.data)

export const updateAdminUser = (userId: string, body: Partial<{ role: string; disabled: boolean }>) =>
  api.patch<{ message: string; user: AuthUser }>(`/admin/users/${userId}`, body).then(r => r.data)

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

export const authGetHistory = () =>
  api.get<{ entries: LoginHistoryEntry[]; total: number }>('/auth/history').then(r => r.data)

export const authGetSessions = () =>
  api.get<{ sessions: UserSession[]; total: number }>('/auth/sessions').then(r => r.data)

export const authRevokeSession = (sessionId: string) =>
  api.delete(`/auth/sessions/${sessionId}`).then(r => r.data)
