import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Claims from './pages/Claims'
import ClaimDetail from './pages/ClaimDetail'
import Chat from './pages/Chat'
import Users from './pages/Users'
import Sync from './pages/Sync'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="claims" element={<Claims />} />
            <Route path="claims/:id" element={<ClaimDetail />} />
            <Route path="chat" element={<Chat />} />
            <Route path="users" element={<Users />} />
            <Route path="sync" element={<Sync />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
