export type UserRole = 'admin' | 'premium' | 'user'

export interface AuthUser {
  id: string
  username: string
  email: string
  role: UserRole
  email_verified: boolean
  twofa_enabled: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

export interface LoginRequest {
  username: string
  password: string
  twofa_code?: string
  device_info?: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface Document {
  id: string
  user_id: string
  filename: string
  file_type: string
  file_size: number
  status: 'uploaded' | 'processing' | 'processed' | 'error'
  chunk_count: number
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface Conversation {
  id: string
  user_id: string
  title: string
  document_ids: string[]
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  sources: Source[]
  created_at: string
}

export interface Source {
  chunk_id: string
  document_id: string
  document_name: string
  content: string
  relevance_score: number
}

export interface ChatRequest {
  conversation_id?: string
  message: string
  document_ids?: string[]
}

export interface ChatResponse {
  message: string
  conversation_id: string
  sources: Source[]
}

export interface AdminStats {
  total_users: number
  total_documents: number
  total_conversations: number
  total_messages: number
  documents_by_type: Record<string, number>
  storage_used_mb: number
}

export interface LoginHistoryEntry {
  id: string
  user_id: string
  ip_address: string
  device_info: string
  success: boolean
  fail_reason: string | null
  timestamp: string
}

export interface UserSession {
  id: string
  user_id: string
  device_info: string
  ip_address: string
  created_at: string
  last_activity: string
  is_active: boolean
}
