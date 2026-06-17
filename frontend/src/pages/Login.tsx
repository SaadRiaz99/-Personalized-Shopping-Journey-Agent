import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'

export default function Login() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (isLogin) {
      const result = await login({ username, password })
      if (result.success) {
        navigate('/')
      } else {
        setError(result.detail || 'Login failed')
      }
    } else {
      if (password.length < 8) {
        setError('Password must be at least 8 characters')
        return
      }
      const result = await register({ username, email, password })
      if (result.success) {
        setIsLogin(true)
        setError('Registration successful! Please login.')
      } else {
        setError(result.detail || 'Registration failed')
      }
    }
  }

  return (
    <div className="login-page">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="login-card"
      >
        <div className="login-header">
          <div className="logo-icon-glow" style={{ width: 48, height: 48 }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1>RAG Document Q&A</h1>
          <p className="text-dim">Intelligent document querying with AI</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="input-group">
            <label>Username</label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Enter username"
              required
            />
          </div>
          {!isLogin && (
            <div className="input-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="Enter email"
                required
              />
            </div>
          )}
          <div className="input-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Enter password"
              required
            />
          </div>
          {error && <div className="error-msg">{error}</div>}
          <button type="submit" className="btn btn-primary" style={{ width: '100%' }}>
            {isLogin ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="login-footer">
          <button className="btn-text" onClick={() => { setIsLogin(!isLogin); setError('') }}>
            {isLogin ? "Don't have an account? Sign up" : 'Already have an account? Sign in'}
          </button>
        </div>

        <div className="demo-creds">
          <p className="text-dim" style={{ fontSize: '0.8rem' }}>Demo: admin / Admin@123</p>
        </div>
      </motion.div>

      <style>{`
        .login-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg);
          padding: 20px;
        }
        .login-card {
          width: 100%;
          max-width: 420px;
          padding: 40px;
          border-radius: 24px;
          background: var(--glass-card);
          border: 1px solid var(--glass-border);
        }
        .login-header { text-align: center; margin-bottom: 32px; }
        .login-header h1 { font-size: 1.5rem; margin-top: 16px; }
        .login-form { display: flex; flex-direction: column; gap: 16px; }
        .input-group { display: flex; flex-direction: column; gap: 6px; }
        .input-group label { font-size: 0.85rem; color: var(--text-dim); font-weight: 600; }
        .input-group input {
          padding: 12px 16px;
          border-radius: 12px;
          border: 1px solid var(--glass-border);
          background: var(--glass-highlight);
          color: var(--text);
          font-size: 0.95rem;
          transition: var(--transition-smooth);
        }
        .input-group input:focus { outline: none; border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-glow); }
        .error-msg { color: var(--danger); font-size: 0.85rem; padding: 8px 12px; border-radius: 8px; background: rgba(255,0,0,0.1); }
        .login-footer { text-align: center; margin-top: 16px; }
        .btn-text { background: none; border: none; color: var(--primary); cursor: pointer; font-size: 0.9rem; }
        .btn-text:hover { text-decoration: underline; }
        .demo-creds { text-align: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--glass-border); }
      `}</style>
    </div>
  )
}
