import { useEffect, useState } from 'react'
import api from '../api'
import { Car, MapPin, Users, Calendar, DollarSign } from 'lucide-react'

function Stat({ label, value, icon: Icon, color }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}><Icon size={22} /></div>
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  useEffect(() => { api.get('/reportes/dashboard').then(r => setStats(r.data)) }, [])

  if (!stats) return <div>Cargando...</div>

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Stat label="Espacios Totales" value={stats.espacios_total} icon={MapPin} color="bg-blue-100 text-blue-700" />
        <Stat label="Espacios Libres" value={stats.espacios_libres} icon={MapPin} color="bg-green-100 text-green-700" />
        <Stat label="Espacios Ocupados" value={stats.espacios_ocupados} icon={MapPin} color="bg-orange-100 text-orange-700" />
        <Stat label="Vehículos Dentro" value={stats.vehiculos_dentro} icon={Car} color="bg-purple-100 text-purple-700" />
        <Stat label="Mensualidades Activas" value={stats.mensualidades_activas} icon={Calendar} color="bg-cyan-100 text-cyan-700" />
        <Stat label="Ingresos Hoy" value={`$${(stats.ingresos_hoy || 0).toLocaleString()}`} icon={DollarSign} color="bg-emerald-100 text-emerald-700" />
      </div>
    </div>
  )
}
