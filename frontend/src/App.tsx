import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import Deals from './pages/Deals'
import Products from './pages/Products'
import Preferences from './pages/Preferences'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="agents" element={<Agents />} />
          <Route path="deals" element={<Deals />} />
          <Route path="products" element={<Products />} />
          <Route path="preferences" element={<Preferences />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
