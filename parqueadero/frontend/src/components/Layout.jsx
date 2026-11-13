import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import {
  LayoutDashboard, Car, MapPin, Users, DollarSign,
  Calendar, Wallet, BarChart3, LogOut, Menu, X
} from 'lucide-react'

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
  const [menuAbierto, setMenuAbierto] = useState(false)

  const cerrarSesion = () => {
    logout()
    nav('/login')
  }

  return (
    <div className="flex min-h-screen bg-slate-100">

      {/* BARRA SUPERIOR PARA MÓVILES */}
      <div className="md:hidden fixed top-0 left-0 right-0 bg-slate-900 text-white p-4 flex justify-between items-center z-50 shadow-md">
        <h1 className="text-xl font-bold">🅿️ Parqueadero</h1>
        <button onClick={() => setMenuAbierto(!menuAbierto)} className="p-1">
          {menuAbierto ? <X size={28} /> : <Menu size={28} />}
        </button>
      </div>

      {/* OVERLAY (Fondo oscuro al abrir menú en celular) */}
      {menuAbierto && (
        <div
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMenuAbierto(false)}
        />
      )}

      {/* BARRA LATERAL (Menú) */}
      <aside className={`
        fixed md:static inset-y-0 left-0 z-50
        w-64 bg-slate-900 text-white flex flex-col transform transition-transform duration-300 ease-in-out
        ${menuAbierto ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="p-5 border-b border-slate-700 hidden md:block">
          <h1 className="text-xl font-bold">🅿️ Parqueadero</h1>
          <p className="text-xs text-slate-400 mt-1">{user?.nombre} · {user?.rol}</p>
        </div>

        <nav className="flex-1 p-3 space-y-1 mt-16 md:mt-0 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={() => setMenuAbierto(false)} // Cierra el menú al elegir opción
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-3 rounded-lg text-sm transition ${isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'
                }`}>
              <Icon size={20} /> {label}
            </NavLink>
          ))}
        </nav>

        <button
          onClick={cerrarSesion}
          className="flex items-center gap-2 px-5 py-4 text-sm text-slate-400 hover:text-white border-t border-slate-700">
          <LogOut size={16} /> Cerrar sesión
        </button>
      </aside>

      {/* CONTENIDO PRINCIPAL */}
      <main className="flex-1 p-4 md:p-6 mt-16 md:mt-0 overflow-x-hidden">
        <div className="max-w-7xl mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}