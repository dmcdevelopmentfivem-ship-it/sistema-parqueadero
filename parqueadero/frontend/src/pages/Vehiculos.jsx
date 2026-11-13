import { useEffect, useState } from 'react'
import api from '../api'

export default function Vehiculos() {
  const [vs, setVs] = useState([])
  const [q, setQ] = useState('')
  const [form, setForm] = useState({ placa: '', tipo: 'carro', marca: '', color: '', propietario: '', telefono: '' })
  const [msg, setMsg] = useState('')

  const cargar = () => {
    api.get(`/vehiculos/?${q ? `q=${q}` : ''}`)
      .then(r => setVs(Array.isArray(r.data) ? r.data : []))
      .catch(() => setVs([]))
  }

  useEffect(() => { cargar() }, [q])

  async function crear(e) {
    e.preventDefault()
    try {
      await api.post('/vehiculos/', form)
      setForm({ placa: '', tipo: 'carro', marca: '', color: '', propietario: '', telefono: '' })
      cargar()
      setMsg('✅ Vehículo registrado')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Vehículos</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-3 gap-3">
        <input className="input" placeholder="Placa" required value={form.placa}
          onChange={e => setForm({ ...form, placa: e.target.value.toUpperCase() })} />
        <select className="input" value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })}>
          <option value="carro">Carro</option><option value="moto">Moto</option><option value="bici">Bicicleta</option>
        </select>
        <input className="input" placeholder="Marca" value={form.marca} onChange={e => setForm({ ...form, marca: e.target.value })} />
        <input className="input" placeholder="Color" value={form.color} onChange={e => setForm({ ...form, color: e.target.value })} />
        <input className="input" placeholder="Propietario" value={form.propietario} onChange={e => setForm({ ...form, propietario: e.target.value })} />
        <input className="input" placeholder="Teléfono" value={form.telefono} onChange={e => setForm({ ...form, telefono: e.target.value })} />
        <button className="btn btn-primary col-span-2 md:col-span-3">Agregar vehículo</button>
      </form>

      <div className="card">
        <input className="input mb-3" placeholder="Buscar por placa..." value={q} onChange={e => setQ(e.target.value)} />
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Placa</th><th>Tipo</th><th>Marca</th><th>Color</th><th>Propietario</th></tr>
          </thead>
          <tbody>
            {Array.isArray(vs) && vs.map(v => (
              <tr key={v.id} className="border-b">
                <td className="py-2 font-bold">{v.placa}</td>
                <td>{v.tipo}</td><td>{v.marca || '-'}</td><td>{v.color || '-'}</td><td>{v.propietario || '-'}</td>
              </tr>
            ))}
            {(!vs || vs.length === 0) && <tr><td colSpan="5" className="py-6 text-center text-slate-400">No hay vehículos</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}