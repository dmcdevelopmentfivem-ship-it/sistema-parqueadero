import { useEffect, useState } from 'react'
import api from '../api'

export default function Mensualidades() {
  const [ms, setMs] = useState([])
  const [form, setForm] = useState({ placa: '', tipo_vehiculo: 'carro', fecha_inicio: '', fecha_fin: '', valor: '' })
  const [msg, setMsg] = useState('')

  const cargar = () => api.get('/mensualidades/').then(r => setMs(r.data))
  useEffect(() => { cargar() }, [])

  async function crear(e) {
    e.preventDefault()
    try {
      await api.post('/mensualidades/', { ...form, valor: +form.valor })
      setForm({ placa: '', tipo_vehiculo: 'carro', fecha_inicio: '', fecha_fin: '', valor: '' })
      cargar()
      setMsg('✅ Mensualidad creada')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Mensualidades</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-5 gap-3">
        <input className="input" placeholder="Placa (ej. ABC123)" required value={form.placa}
          onChange={e => setForm({ ...form, placa: e.target.value.toUpperCase() })} />
        <select className="input" value={form.tipo_vehiculo} onChange={e => setForm({ ...form, tipo_vehiculo: e.target.value })}>
          <option value="carro">Carro</option>
          <option value="moto">Moto</option>
          <option value="bici">Bicicleta</option>
        </select>
        <input className="input" type="date" required value={form.fecha_inicio} onChange={e => setForm({ ...form, fecha_inicio: e.target.value })} />
        <input className="input" type="date" required value={form.fecha_fin} onChange={e => setForm({ ...form, fecha_fin: e.target.value })} />
        <input className="input" type="number" placeholder="Valor" required value={form.valor} onChange={e => setForm({ ...form, valor: e.target.value })} />
        <button className="btn btn-primary col-span-2 md:col-span-5">Crear mensualidad</button>
      </form>

      <div className="card">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">ID</th><th>Placa</th><th>Inicio</th><th>Fin</th><th>Valor</th><th>Estado</th></tr>
          </thead>
          <tbody>
            {ms.map(m => (
              <tr key={m.id} className="border-b">
                <td className="py-2">#{m.id}</td>
                <td className="font-bold text-slate-800">{m.placa || `#${m.vehiculo_id}`}</td>
                <td>{m.fecha_inicio}</td><td>{m.fecha_fin}</td>
                <td>${(+m.valor).toLocaleString()}</td>
                <td><span className={`px-2 py-1 rounded text-xs ${m.estado === 'activa' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{m.estado}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
