import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { authMe, authLogin, authRegister, authLogout } from '../services/api'
import type { AuthUser, LoginRequest, RegisterRequest } from '../types'

interface AuthContextType {
  user: AuthUser | null
  loading: boolean
  login: (body: LoginRequest) => Promise<{ success: boolean; twofa_required?: boolean; detail?: string }>
  register: (body: RegisterRequest) => Promise<{ success: boolean; detail?: string }>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const u = await authMe()
      setUser(u)
    } catch {
      setUser(null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }
    setLoading(false)
  }

  useEffect(() => {
    let cancelled = false
    refreshUser().then(() => { if (cancelled) { setUser(null); setLoading(false) } })
    return () => { cancelled = true }
  }, [])

  const login = async (body: LoginRequest) => {
    try {
      const res = await authLogin(body)
      localStorage.setItem('access_token', res.access_token)
      localStorage.setItem('refresh_token', res.refresh_token)
      localStorage.setItem('user', JSON.stringify(res.user))
      setUser(res.user)
      return { success: true }
    } catch (err: unknown) {
      const detail = (err as { response?: { status?: number; data?: { detail?: string } } })?.response?.data?.detail || 'Login failed'
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 428) {
        return { success: false, detail, twofa_required: true }
      }
      return { success: false, detail }
    }
  }

  const register = async (body: RegisterRequest) => {
    try {
      await authRegister(body)
      return { success: true }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Registration failed'
      return { success: false, detail }
    }
  }

  const logout = async () => {
    try { await authLogout() } catch { /* ignore */ }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
