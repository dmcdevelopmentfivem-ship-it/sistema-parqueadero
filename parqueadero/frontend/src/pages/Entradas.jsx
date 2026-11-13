import { useEffect, useState } from 'react'
import api from '../api'
import { Plus, LogOut } from 'lucide-react'

export default function Entradas() {
  const [activas, setActivas] = useState([])
  const [form, setForm] = useState({ placa: '', tipo_vehiculo: 'carro' })
  const [msg, setMsg] = useState('')

  const cargar = () => api.get('/entradas/activas')
    .then(r => setActivas(Array.isArray(r.data) ? r.data : []))
    .catch(() => setActivas([]))
  useEffect(() => { cargar() }, [])

  async function entrada(e) {
    e.preventDefault()
    setMsg('')
    try {
      await api.post('/entradas/entrada', form)
      setForm({ placa: '', tipo_vehiculo: 'carro' })
      cargar()
      setMsg('✅ Entrada registrada')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  async function salida(id) {
    try {
      const calc = await api.get(`/entradas/calcular/${id}`)
      const valor = calc.data.valor
      if (!confirm(`Cobrar $${valor}?`)) return
      const { data } = await api.post(`/entradas/salida/${id}`, { metodo_pago: 'efectivo' })
      setMsg(`✅ Salida: ${data.placa} - $${Number(data.valor || 0).toLocaleString()} (cambio: $${Number(data.cambio || 0).toLocaleString()})`)
      cargar()
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Entradas / Salidas</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={entrada} className="card mb-5 flex gap-3 items-end flex-wrap">
        <div>
          <label className="text-sm">Placa</label>
          <input className="input" value={form.placa} required
            onChange={e => setForm({ ...form, placa: e.target.value.toUpperCase() })} />
        </div>
        <div>
          <label className="text-sm">Tipo</label>
          <select className="input" value={form.tipo_vehiculo}
            onChange={e => setForm({ ...form, tipo_vehiculo: e.target.value })}>
            <option value="carro">Carro</option>
            <option value="moto">Moto</option>
            <option value="bici">Bicicleta</option>
          </select>
        </div>
        <button className="btn btn-primary flex items-center gap-2"><Plus size={16} /> Registrar Entrada</button>
      </form>

      <div className="card overflow-x-auto">
        <h3 className="font-semibold mb-3">Vehículos dentro ({Array.isArray(activas) ? activas.length : 0})</h3>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Ticket</th><th>Placa</th><th>Tipo</th><th>Espacio</th><th>Entrada</th><th></th></tr>
          </thead>
          <tbody>
            {(Array.isArray(activas) ? activas : []).map(o => (
              <tr key={o.id} className="border-b hover:bg-slate-50">
                <td className="py-2">#{o.id}</td>
                <td className="font-bold text-slate-800">{o.placa || `#${o.vehiculo_id}`}</td>
                <td><span className="uppercase text-xs font-semibold px-2 py-0.5 bg-slate-100 rounded text-slate-700">{o.tipo_vehiculo || '-'}</span></td>
                <td><span className="px-2 py-0.5 bg-blue-50 text-blue-700 font-medium rounded text-xs">{o.espacio_codigo || (o.espacio_id ? `#${o.espacio_id}` : '-')}</span></td>
                <td>{new Date(o.hora_entrada).toLocaleString()}</td>
                <td>
                  <button onClick={() => salida(o.id)} className="btn btn-danger text-xs flex items-center gap-1">
                    <LogOut size={12} /> Salida
                  </button>
                </td>
              </tr>
            ))}
            {(!Array.isArray(activas) || !activas.length) && <tr><td colSpan="6" className="py-6 text-center text-slate-400">Sin vehículos dentro</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
