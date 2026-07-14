import { useState, useEffect, useRef } from 'react'
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
  const mouseRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (user) navigate('/', { replace: true })
  }, [user, navigate])

  useEffect(() => {
    const el = mouseRef.current
    if (!el) return
    const handler = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect()
      el.style.setProperty('--mx', `${e.clientX - rect.left}px`)
      el.style.setProperty('--my', `${e.clientY - rect.top}px`)
    }
    el.addEventListener('mousemove', handler)
    return () => el.removeEventListener('mousemove', handler)
  }, [])

  const showError = (text: string) => setMessage({ type: 'error', text })
  const showSuccess = (text: string) => setMessage({ type: 'success', text })
  const showInfo = (text: string) => setMessage({ type: 'info', text })

  const handleLogin = async () => {
    if (!username || !password) { showError('Please fill in all fields'); return }
    setSubmitting(true); setMessage(null)
    const result = await login({ username, password, device_info: navigator.userAgent })
    if (result.success) { showSuccess('Login successful! Redirecting...'); setTimeout(() => navigate('/', { replace: true }), 500) }
    else if (result.twofa_required) { setMode('twofa'); showInfo('Enter your 2FA code to continue') }
    else { showError(result.detail || 'Login failed') }
    setSubmitting(false)
  }

  const handleTwoFA = async () => {
    if (!twofaCode) { showError('Enter your 2FA code'); return }
    setSubmitting(true); setMessage(null)
    const result = await login({ username, password, twofa_code: twofaCode, device_info: navigator.userAgent })
    if (result.success) { showSuccess('Login successful! Redirecting...'); setTimeout(() => navigate('/', { replace: true }), 500) }
    else { showError(result.detail || 'Invalid 2FA code') }
    setSubmitting(false)
  }

  const handleRegister = async () => {
    if (!username || !email || !password) { showError('Please fill in all fields'); return }
    if (password !== confirmPassword) { showError('Passwords do not match'); return }
    setSubmitting(true); setMessage(null)
    const result = await register({ username, email, password })
    if (result.success) { showSuccess('Registration successful! You can now log in.'); setMode('login'); setPassword(''); setConfirmPassword('') }
    else { showError(result.detail || 'Registration failed') }
    setSubmitting(false)
  }

  const switchMode = (m: Mode) => { setMode(m); setMessage(null); setTwofaCode('') }

  return (
    <div ref={mouseRef} style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg)', padding: '1rem', position: 'relative', overflow: 'hidden',
      '--mx': '50%', '--my': '50%',
    } as React.CSSProperties}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
        background: 'radial-gradient(600px circle at var(--mx, 50%) var(--my, 50%), rgba(129,140,248,0.04), transparent 60%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', top: '-30%', left: '-10%', width: '50%', height: '80%',
        background: 'radial-gradient(ellipse, rgba(99,102,241,0.06), transparent 70%)',
        filter: 'blur(60px)', pointerEvents: 'none',
      }} />

      <motion.div initial={{ opacity: 0, y: 30, scale: 0.96 }} animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: 'spring', damping: 25, stiffness: 150 }}
        className="glass-panel" style={{ width: '100%', maxWidth: 420, padding: '2.5rem', position: 'relative' }}>

        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div className="logo-icon-glow" style={{ width: 52, height: 52, margin: '0 auto 1rem' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.03em',
            background: 'linear-gradient(135deg, var(--text) 0%, var(--text-muted) 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
          }}>ShopOrch</h1>
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginTop: '0.35rem' }}>Personalized Shopping Agent</p>
        </div>

        <AnimatePresence mode="wait">
          {mode === 'login' && (
            <motion.div key="login" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 16 }}
              transition={{ duration: 0.2 }}>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label htmlFor="login-username">Username</label>
                <input id="login-username" className="input" value={username} onChange={e => setUsername(e.target.value)}
                  placeholder="admin / premium_user / user1" autoFocus />
              </div>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="login-password">Password</label>
                <input id="login-password" className="input" type="password" value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password" onKeyDown={e => e.key === 'Enter' && handleLogin()} />
              </div>
              {message && <div className={message.type === 'error' ? 'alert alert-error' : message.type === 'success' ? 'alert alert-success' : 'alert alert-info'} role="alert" style={{ marginBottom: '0.75rem' }}>{message.text}</div>}
              <button className="btn-cyber" onClick={handleLogin} disabled={submitting}
                style={{ width: '100%', height: 44, borderRadius: 'var(--radius-md)' }}>
                {submitting ? <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}><span className="spinner" /> Signing in...</span> : 'Sign In'}
              </button>
              <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.82rem', color: 'var(--text-dim)' }}>
                Don't have an account?{' '}
                <button onClick={() => switchMode('register')}
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontWeight: 600, padding: 0 }}>Register</button>
              </p>
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'var(--primary-subtle)', borderRadius: 'var(--radius-sm)', fontSize: '0.72rem', color: 'var(--text-dim)', border: '1px solid rgba(129,140,248,0.08)' }}>
                <strong style={{ color: 'var(--text-muted)' }}>Demo accounts:</strong><br />
                admin / Admin@123 {"\u2014"} Full access<br />
                premium_user / Premium@123 {"\u2014"} Premium<br />
                user1 / User@1234 {"\u2014"} Standard
              </div>
            </motion.div>
          )}

          {mode === 'twofa' && (
            <motion.div key="twofa" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 16 }}
              transition={{ duration: 0.2 }}>
              <p style={{ fontSize: '0.9rem', marginBottom: '0.75rem', color: 'var(--text-muted)' }}>Two-factor authentication</p>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="twofa-code">Authentication Code</label>
                <input id="twofa-code" className="input" value={twofaCode} onChange={e => setTwofaCode(e.target.value)}
                  placeholder="000000" maxLength={6} autoFocus onKeyDown={e => e.key === 'Enter' && handleTwoFA()}
                  style={{ fontSize: '1.2rem', letterSpacing: '0.3em', textAlign: 'center' }} />
              </div>
              {message && <div className={message.type === 'error' ? 'alert alert-error' : 'alert alert-info'} role="alert" style={{ marginBottom: '0.75rem' }}>{message.text}</div>}
              <button className="btn-cyber" onClick={handleTwoFA} disabled={submitting}
                style={{ width: '100%', height: 44, borderRadius: 'var(--radius-md)' }}>
                {submitting ? <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}><span className="spinner" /> Verifying...</span> : 'Verify Code'}
              </button>
              <button className="btn btn-ghost" onClick={() => switchMode('login')}
                style={{ width: '100%', marginTop: '0.5rem' }}>Back to login</button>
            </motion.div>
          )}

          {mode === 'register' && (
            <motion.div key="register" initial={{ opacity: 0, x: -16 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 16 }}
              transition={{ duration: 0.2 }}>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label htmlFor="reg-username">Username</label>
                <input id="reg-username" className="input" value={username} onChange={e => setUsername(e.target.value)}
                  placeholder="Choose a username" autoFocus />
              </div>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label htmlFor="reg-email">Email</label>
                <input id="reg-email" className="input" type="email" value={email} onChange={e => setEmail(e.target.value)}
                  placeholder="your@email.com" />
              </div>
              <div className="form-group" style={{ marginBottom: '0.75rem' }}>
                <label htmlFor="reg-password">Password</label>
                <input id="reg-password" className="input" type="password" value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="Min 8 chars, upper, lower, digit, special" />
              </div>
              <div className="form-group" style={{ marginBottom: '1rem' }}>
                <label htmlFor="reg-confirm">Confirm Password</label>
                <input id="reg-confirm" className="input" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password" onKeyDown={e => e.key === 'Enter' && handleRegister()} />
              </div>
              {message && <div className={message.type === 'error' ? 'alert alert-error' : 'alert alert-success'} role="alert" style={{ marginBottom: '0.75rem' }}>{message.text}</div>}
              <button className="btn-cyber" onClick={handleRegister} disabled={submitting}
                style={{ width: '100%', height: 44, borderRadius: 'var(--radius-md)' }}>
                {submitting ? <span style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'center' }}><span className="spinner" /> Creating...</span> : 'Create Account'}
              </button>
              <p style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.82rem', color: 'var(--text-dim)' }}>
                Already have an account?{' '}
                <button onClick={() => switchMode('login')}
                  style={{ background: 'none', border: 'none', color: 'var(--primary)', cursor: 'pointer', fontWeight: 600, padding: 0 }}>Sign in</button>
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
