import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const links = [
  { 
    to: '/', 
    label: 'Council', 
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" /><path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    )
  },
  { 
    to: '/agents', 
    label: 'Agents', 
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="9" y1="3" x2="9" y2="21" />
      </svg>
    )
  },
  { 
    to: '/catalog', 
    label: 'Catalog', 
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
        <polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" />
      </svg>
    )
  },
  { 
    to: '/deals', 
    label: 'Deals', 
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" /><line x1="7" y1="7" x2="7.01" y2="7" />
      </svg>
    )
  },
  { 
    to: '/price-match', 
    label: 'Prices', 
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
      </svg>
    )
  },
  { 
    to: '/preferences', 
    label: 'Settings', 
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
      </svg>
    )
  },
]

export default function Layout() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')
  const location = useLocation()

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')

  return (
    <div className="layout">
      <motion.nav 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="sidebar"
      >
        <div className="logo-container">
          <div className="logo-icon-glow">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" /></svg>
          </div>
          <span style={{ fontWeight: 800, fontSize: '1.25rem' }}>ShopOrch</span>
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {links.map((l, i) => (
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
        {links.map(l => (
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
          borderRadius: 12px;
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
      `}</style>
    </div>
  )
}
