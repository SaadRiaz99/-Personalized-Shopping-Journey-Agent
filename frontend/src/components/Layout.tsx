import { NavLink, Outlet } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard', icon: '◉' },
  { to: '/agents', label: 'Agents', icon: '◆' },
  { to: '/products', label: 'Products', icon: '✦' },
  { to: '/preferences', label: 'Preferences', icon: '⚙' },
]

export default function Layout() {
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
        <div className="sidebar-footer">
          <p>Personalized Shopping Agent</p>
        </div>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
