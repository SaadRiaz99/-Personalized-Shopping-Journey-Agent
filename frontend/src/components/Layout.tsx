import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../contexts/AuthContext'

const links = [
  {
    to: '/',
    label: 'Chat',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
  },
  {
    to: '/documents',
    label: 'Documents',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    to: '/conversations',
    label: 'History',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
  },
  {
    to: '/admin',
    label: 'Admin',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
  },
  {
    to: '/account',
    label: 'Account',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
        <circle cx="12" cy="7" r="4" />
      </svg>
    ),
  },
]

export default function Layout() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')
  const location = useLocation()
  const { user } = useAuth()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')

  const filteredLinks = links.filter(l => {
    if (l.to === '/admin') return user?.role === 'admin'
    return true
  })

  return (
    <div className="layout">
      <motion.nav
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="sidebar"
      >
        <div className="logo-container">
          <div className="logo-icon-glow">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
            </svg>
          </div>
          <span style={{ fontWeight: 800, fontSize: '1.25rem' }}>RAG Q&A</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {filteredLinks.map((l, i) => (
            <motion.div key={l.to} initial={{ x: -20, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: i * 0.1 }}>
              <NavLink to={l.to} className={({ isActive }) => isActive ? 'sidebar-link active' : 'sidebar-link'}>
                <div style={{ width: '20px', height: '20px' }}>{l.icon}</div>
                {l.label}
              </NavLink>
            </motion.div>
          ))}
        </div>

        <button className="btn btn-cyber" onClick={toggleTheme} style={{ marginTop: 'auto', background: 'rgba(255,255,255,0.03)', border: '1px solid var(--glass-border)' }}>
          {theme === 'light' ? '🌙 Dark' : '☀️ Light'}
        </button>
      </motion.nav>

      <nav className="mobile-nav">
        {filteredLinks.map(l => (
          <NavLink key={l.to} to={l.to} className={({ isActive }) => isActive ? 'mobile-link active' : 'mobile-link'}>
            <div style={{ width: '24px', height: '24px', margin: '0 auto' }}>{l.icon}</div>
          </NavLink>
        ))}
        <button onClick={toggleTheme} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', fontSize: '1.2rem' }}>
          {theme === 'light' ? '🌙' : '☀️'}
        </button>
      </nav>

      <main className="content">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 120 }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      <style>{`
        .sidebar-link {
          display: flex;
          align-items: center;
          gap: 14px;
          padding: 12px 16px;
          border-radius: 12px;
          color: var(--text-muted);
          text-decoration: none;
          font-size: 0.95rem;
          font-weight: 600;
          transition: var(--transition-smooth);
        }
        .sidebar-link:hover { background: var(--glass-highlight); color: var(--text); transform: translateX(5px); }
        .sidebar-link.active { background: var(--primary-glow) !important; color: var(--primary) !important; border: 1px solid var(--primary); }

        .mobile-link { color: var(--text-dim); transition: var(--transition-smooth); }
        .mobile-link.active { color: var(--primary); transform: scale(1.2); filter: drop-shadow(0 0 8px var(--primary)); }

        .loading-screen {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 100vh;
          background: var(--bg);
        }
        .spinner {
          width: 40px;
          height: 40px;
          border: 3px solid var(--glass-border);
          border-top-color: var(--primary);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
