import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Agents from './pages/Agents'
import CatalogSearch from './pages/CatalogSearch'
import Deals from './pages/Deals'
import GiftFinder from './pages/GiftFinder'
import CrossSell from './pages/CrossSell'
import PriceMatch from './pages/PriceMatch'
import Products from './pages/Products'
import Recommendations from './pages/Recommendations'
import Preferences from './pages/Preferences'
import Account from './pages/Account'
import BudgetTracker from './pages/BudgetTracker'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="agents" element={<Agents />} />
              <Route path="catalog" element={<CatalogSearch />} />
              <Route path="deals" element={<Deals />} />
              <Route path="gift-finder" element={<GiftFinder />} />
              <Route path="cross-sell" element={<CrossSell />} />
              <Route path="price-match" element={<PriceMatch />} />
              <Route path="products" element={<Products />} />
              <Route path="recommendations" element={<Recommendations />} />
              <Route path="preferences" element={<Preferences />} />
              <Route path="budget" element={<BudgetTracker />} />
              <Route path="account" element={<Account />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
