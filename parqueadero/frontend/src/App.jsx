import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './auth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Entradas from './pages/Entradas'
import Espacios from './pages/Espacios'
import Vehiculos from './pages/Vehiculos'
import Tarifas from './pages/Tarifas'
import Mensualidades from './pages/Mensualidades'
import Contabilidad from './pages/Contabilidad'
import Reportes from './pages/Reportes'

function Private({ children }) {
  const { token } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Private><Dashboard /></Private>} />
      <Route path="/entradas" element={<Private><Entradas /></Private>} />
      <Route path="/espacios" element={<Private><Espacios /></Private>} />
      <Route path="/vehiculos" element={<Private><Vehiculos /></Private>} />
      <Route path="/tarifas" element={<Private><Tarifas /></Private>} />
      <Route path="/mensualidades" element={<Private><Mensualidades /></Private>} />
      <Route path="/contabilidad" element={<Private><Contabilidad /></Private>} />
      <Route path="/reportes" element={<Private><Reportes /></Private>} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
