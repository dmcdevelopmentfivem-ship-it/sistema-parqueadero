import { useEffect, useState } from 'react'
import api from '../api'

export default function Mensualidades() {
  const [ms, setMs] = useState([])
  const [form, setForm] = useState({ vehiculo_id: '', fecha_inicio: '', fecha_fin: '', valor: 0 })
  const [msg, setMsg] = useState('')

  const cargar = () => {
    api.get('/mensualidades/')
      .then(r => setMs(Array.isArray(r.data) ? r.data : []))
      .catch(() => setMs([]))
  }

  useEffect(() => { cargar() }, [])

  async function crear(e) {
    e.preventDefault()
    try {
      await api.post('/mensualidades/', { ...form, vehiculo_id: +form.vehiculo_id, valor: +form.valor })
      cargar()
      setMsg('✅ Mensualidad creada')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Mensualidades</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        <input className="input" type="number" placeholder="ID Vehículo" required value={form.vehiculo_id} onChange={e => setForm({ ...form, vehiculo_id: e.target.value })} />
        <input className="input" type="date" required value={form.fecha_inicio} onChange={e => setForm({ ...form, fecha_inicio: e.target.value })} />
        <input className="input" type="date" required value={form.fecha_fin} onChange={e => setForm({ ...form, fecha_fin: e.target.value })} />
        <input className="input" type="number" placeholder="Valor" required value={form.valor} onChange={e => setForm({ ...form, valor: e.target.value })} />
        <button className="btn btn-primary col-span-2 md:col-span-4">Crear mensualidad</button>
      </form>

      <div className="card">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">ID</th><th>Vehículo</th><th>Inicio</th><th>Fin</th><th>Valor</th><th>Estado</th></tr>
          </thead>
          <tbody>
            {Array.isArray(ms) && ms.map(m => (
              <tr key={m.id} className="border-b">
                <td className="py-2">#{m.id}</td><td>#{m.vehiculo_id}</td>
                <td>{m.fecha_inicio}</td><td>{m.fecha_fin}</td>
                <td>${Number(m.valor || 0).toLocaleString()}</td>
                <td><span className={`px-2 py-1 rounded text-xs ${m.estado === 'activa' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{m.estado}</span></td>
              </tr>
            ))}
            {(!ms || ms.length === 0) && <tr><td colSpan="6" className="py-6 text-center text-slate-400">Sin mensualidades</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}