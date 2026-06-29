import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'

type Mode = 'login' | 'register' | 'twofa'

export default function Login() {
  const { login, register, user } = useAuth()
  const navigate = useNavigate()

  const [mode, setMode] = useState<Mode>('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [twofaCode, setTwofaCode] = useState('')
  const [message, setMessage] = useState<{ type: 'error' | 'success' | 'info'; text: string } | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (user) {
    navigate('/', { replace: true })
    return null
  }

  const showError = (text: string) => setMessage({ type: 'error', text })
  const showSuccess = (text: string) => setMessage({ type: 'success', text })
  const showInfo = (text: string) => setMessage({ type: 'info', text })

  const handleLogin = async () => {
    if (!username || !password) { showError('Please fill in all fields'); return }
    setSubmitting(true)
    setMessage(null)
    const result = await login({ username, password, device_info: navigator.userAgent })
    if (result.success) {
      showSuccess('Login successful! Redirecting...')
      setTimeout(() => navigate('/', { replace: true }), 500)
    } else if (result.twofa_required) {
      setMode('twofa')
      showInfo('Enter your 2FA code to continue')
    } else {
      showError(result.detail || 'Login failed')
    }
    setSubmitting(false)
  }

  const handleTwoFA = async () => {
    if (!twofaCode) { showError('Enter your 2FA code'); return }
    setSubmitting(true)
    setMessage(null)
    const result = await login({ username, password, twofa_code: twofaCode, device_info: navigator.userAgent })
    if (result.success) {
      showSuccess('Login successful! Redirecting...')
      setTimeout(() => navigate('/', { replace: true }), 500)
    } else {
      showError(result.detail || 'Invalid 2FA code')
    }
    setSubmitting(false)
  }

  const handleRegister = async () => {
    if (!username || !email || !password) { showError('Please fill in all fields'); return }
    if (password !== confirmPassword) { showError('Passwords do not match'); return }
    setSubmitting(true)
    setMessage(null)
    const result = await register({ username, email, password })
    if (result.success) {
      showSuccess('Registration successful! You can now log in.')
      setMode('login')
      setPassword('')
      setConfirmPassword('')
    } else {
      showError(result.detail || 'Registration failed')
    }
    setSubmitting(false)
  }

  const switchMode = (m: Mode) => {
    setMode(m)
    setMessage(null)
    setTwofaCode('')
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'radial-gradient(ellipse at top, #1a1a3e 0%, #0d0d1a 100%)', padding: '1rem',
    }}>
      <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
        className="card" style={{ width: '100%', maxWidth: 420, padding: '2rem' }} role="region" aria-label="Login form">

        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <div className="logo-icon-glow" style={{ width: 56, height: 56, margin: '0 auto 0.75rem' }} aria-hidden="true">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" aria-hidden="true">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>ShopOrch</h1>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginTop: '0.25rem' }}>Personalized Shopping Agent</p>
        </div>

        <AnimatePresence mode="wait">
          {mode === 'login' && (
            <motion.div key="login" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label htmlFor="login-username">Username</label>
                <input id="login-username" className="input" value={username} onChange={e => setUsername(e.target.value)}
                  placeholder="admin / premium_user / user1" autoFocus aria-label="Username" />
              </div>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="login-password">Password</label>
                <input id="login-password" className="input" type="password" value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password" onKeyDown={e => e.key === 'Enter' && handleLogin()} aria-label="Password" />
              </div>
              {message && <div className={`alert alert-${message.type}`} role="alert" style={{ marginBottom: '0.75rem' }}>{message.text}</div>}
              <button className="btn btn-primary" onClick={handleLogin} disabled={submitting}
                style={{ width: '100%', height: 40 }} aria-label="Sign in">
                {submitting ? 'Signing in...' : 'Sign In'}
              </button>
              <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                Don't have an account?{' '}
                <button className="btn" onClick={() => switchMode('register')}
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
                  aria-label="Register new account">
                  Register
                </button>
              </p>
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(99,102,241,0.08)', borderRadius: 8, fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                <strong>Demo accounts:</strong><br />
                admin / Admin@123 — Full access<br />
                premium_user / Premium@123 — Premium access<br />
                user1 / User@1234 — Standard user
              </div>
            </motion.div>
          )}

          {mode === 'twofa' && (
            <motion.div key="twofa" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem' }}>Two-factor authentication</p>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="twofa-code">Authentication Code</label>
                <input id="twofa-code" className="input" value={twofaCode} onChange={e => setTwofaCode(e.target.value)}
                  placeholder="000000" maxLength={6} autoFocus
                  onKeyDown={e => e.key === 'Enter' && handleTwoFA()} aria-label="2FA code" />
              </div>
              {message && <div className={`alert alert-${message.type}`} role="alert" style={{ marginBottom: '0.75rem' }}>{message.text}</div>}
              <button className="btn btn-primary" onClick={handleTwoFA} disabled={submitting}
                style={{ width: '100%', height: 40 }} aria-label="Verify 2FA code">
                {submitting ? 'Verifying...' : 'Verify Code'}
              </button>
              <button className="btn" onClick={() => switchMode('login')}
                style={{ width: '100%', marginTop: '0.5rem', background: 'transparent' }} aria-label="Back to login">
                Back to login
              </button>
            </motion.div>
          )}

          {mode === 'register' && (
            <motion.div key="register" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label htmlFor="reg-username">Username</label>
                <input id="reg-username" className="input" value={username} onChange={e => setUsername(e.target.value)}
                  placeholder="Choose a username (3-32 chars)" autoFocus aria-label="Choose username" />
              </div>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label htmlFor="reg-email">Email</label>
                <input id="reg-email" className="input" type="email" value={email} onChange={e => setEmail(e.target.value)}
                  placeholder="your@email.com" aria-label="Email address" />
              </div>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label htmlFor="reg-password">Password</label>
                <input id="reg-password" className="input" type="password" value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="Min 8 chars, upper, lower, digit, special" aria-label="Password" />
              </div>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="reg-confirm">Confirm Password</label>
                <input id="reg-confirm" className="input" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password" onKeyDown={e => e.key === 'Enter' && handleRegister()} aria-label="Confirm password" />
              </div>
              {message && <div className={`alert alert-${message.type}`} role="alert" style={{ marginBottom: '0.75rem' }}>{message.text}</div>}
              <button className="btn btn-primary" onClick={handleRegister} disabled={submitting}
                style={{ width: '100%', height: 40 }} aria-label="Create account">
                {submitting ? 'Creating account...' : 'Create Account'}
              </button>
              <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.85rem', color: 'var(--text-dim)' }}>
                Already have an account?{' '}
                <button className="btn" onClick={() => switchMode('login')}
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
                  aria-label="Sign in instead">
                  Sign in
                </button>
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
