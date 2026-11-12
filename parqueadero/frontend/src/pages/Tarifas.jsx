import { useEffect, useState } from 'react'
import api from '../api'

export default function Tarifas() {
  const [ts, setTs] = useState([])
  const [form, setForm] = useState({ nombre: '', tipo_vehiculo: 'carro', valor_hora: 0, valor_fraccion: 0, minutos_fraccion: 15, valor_dia: 0 })
  const [msg, setMsg] = useState('')

  const cargar = () => api.get('/tarifas/').then(r => setTs(r.data))
  useEffect(() => { cargar() }, [])

  async function crear(e) {
    e.preventDefault()
    try {
      await api.post('/tarifas/', form)
      cargar()
      setMsg('✅ Tarifa creada')
    } catch (err) { setMsg('❌ ' + (err.response?.data?.detail || 'Error')) }
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Tarifas</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-3 gap-3">
        <input className="input" placeholder="Nombre" required value={form.nombre} onChange={e => setForm({ ...form, nombre: e.target.value })} />
        <select className="input" value={form.tipo_vehiculo} onChange={e => setForm({ ...form, tipo_vehiculo: e.target.value })}>
          <option value="carro">Carro</option><option value="moto">Moto</option><option value="bici">Bicicleta</option>
        </select>
        <input className="input" type="number" placeholder="Valor hora" value={form.valor_hora} onChange={e => setForm({ ...form, valor_hora: +e.target.value })} />
        <input className="input" type="number" placeholder="Valor fracción" required value={form.valor_fraccion} onChange={e => setForm({ ...form, valor_fraccion: +e.target.value })} />
        <input className="input" type="number" placeholder="Minutos fracción" value={form.minutos_fraccion} onChange={e => setForm({ ...form, minutos_fraccion: +e.target.value })} />
        <input className="input" type="number" placeholder="Valor día" required value={form.valor_dia} onChange={e => setForm({ ...form, valor_dia: +e.target.value })} />
        <button className="btn btn-primary col-span-2 md:col-span-3">Crear tarifa</button>
      </form>

      <div className="card">
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Tipo</th><th>Nombre</th><th>Hora</th><th>Fracción</th><th>Día</th><th>Activa</th></tr>
          </thead>
          <tbody>
            {ts.map(t => (
              <tr key={t.id} className="border-b">
                <td className="py-2 font-bold uppercase">{t.tipo_vehiculo}</td>
                <td>{t.nombre}</td><td>${t.valor_hora}</td>
                <td>${t.valor_fraccion}/{t.minutos_fraccion}min</td>
                <td>${t.valor_dia}</td>
                <td>{t.activa ? '✅' : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
