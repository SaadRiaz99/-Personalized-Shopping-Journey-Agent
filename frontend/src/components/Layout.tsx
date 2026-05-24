import { NavLink, Outlet } from 'react-router-dom'
import { useState, useEffect } from 'react'

const links = [
  { to: '/', label: 'Dashboard', icon: '◉' },
  { to: '/agents', label: 'Agents', icon: '◆' },
  { to: '/catalog', label: 'Catalog', icon: '📦' },
  { to: '/deals', label: 'Deals', icon: '💰' },
  { to: '/products', label: 'Products', icon: '✦' },
  { to: '/preferences', label: 'Preferences', icon: '⚙' },
]

export default function Layout() {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark')

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light')

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="logo">
          <div className="logo-icon">◈</div>
          <span>ShopOrch</span>
        </div>
        <div>
          <p className="nav-label">Navigation</p>
          <ul>
            {links.map(l => (
              <li key={l.to}>
                <NavLink to={l.to} className={({ isActive }) => isActive ? 'active' : ''}>
                  <span className="nav-icon">{l.icon}</span>
                  {l.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>

        <div style={{ marginTop: 'auto' }}>
          <button className="btn btn-ghost" onClick={toggleTheme} style={{ width: '100%', justifyContent: 'flex-start', padding: '0.75rem 1rem' }}>
            <span className="nav-icon">{theme === 'light' ? '🌙' : '☀️'}</span>
            {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
          </button>
        </div>

        <div className="sidebar-footer" style={{ borderTop: 'none', paddingTop: 0 }}>
          <p>Personalized Shopping Agent</p>
        </div>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
