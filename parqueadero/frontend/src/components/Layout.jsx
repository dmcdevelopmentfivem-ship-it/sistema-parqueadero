import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { LayoutDashboard, Car, MapPin, Users, DollarSign, Calendar, Wallet, BarChart3, LogOut } from 'lucide-react'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/entradas', label: 'Entradas/Salidas', icon: Car },
  { to: '/espacios', label: 'Espacios', icon: MapPin },
  { to: '/vehiculos', label: 'Vehículos', icon: Users },
  { to: '/tarifas', label: 'Tarifas', icon: DollarSign },
  { to: '/mensualidades', label: 'Mensualidades', icon: Calendar },
  { to: '/contabilidad', label: 'Contabilidad', icon: Wallet },
  { to: '/reportes', label: 'Reportes', icon: BarChart3 },
]

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const nav = useNavigate()

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 bg-slate-900 text-white flex flex-col">
        <div className="p-5 border-b border-slate-700">
          <h1 className="text-xl font-bold">🅿️ Parqueadero</h1>
          <p className="text-xs text-slate-400 mt-1">{user?.nombre} · {user?.rol}</p>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition ${
                  isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'
                }`}>
              <Icon size={18} /> {label}
            </NavLink>
          ))}
        </nav>
        <button onClick={() => { logout(); nav('/login') }}
          className="flex items-center gap-2 px-5 py-3 text-sm text-slate-400 hover:text-white border-t border-slate-700">
          <LogOut size={16} /> Cerrar sesión
        </button>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}
