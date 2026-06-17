import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Chat from './pages/Chat'
import Documents from './pages/Documents'
import Conversations from './pages/Conversations'
import Admin from './pages/Admin'
import Account from './pages/Account'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route index element={<Chat />} />
              <Route path="documents" element={<Documents />} />
              <Route path="conversations" element={<Conversations />} />
              <Route path="admin" element={<Admin />} />
              <Route path="account" element={<Account />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
