import { useEffect, useState } from 'react'
import api from '../api'
import { Plus, LogOut, Search } from 'lucide-react'

export default function Entradas() {
  const [activas, setActivas] = useState([])
  const [form, setForm] = useState({ placa: '', tipo_vehiculo: 'carro' })
  const [msg, setMsg] = useState('')
  const [buscar, setBuscar] = useState('')

  const cargar = () => {
    api.get('/entradas/activas')
      .then(r => {
        if (Array.isArray(r.data)) setActivas(r.data)
        else setActivas([])
      })
      .catch(err => {
        console.error(err)
        setActivas([])
      })
  }

  useEffect(() => { cargar() }, [])

  async function entrada(e) {
    e.preventDefault()
    setMsg('')
    try {
      await api.post('/entradas/entrada', {
        placa: form.placa.toUpperCase().trim(),
        tipo_vehiculo: form.tipo_vehiculo
      })
      setForm({ placa: '', tipo_vehiculo: 'carro' })
      cargar()
      setMsg('✅ Entrada registrada correctamente')
    } catch (err) {
      setMsg('❌ ' + (err.response?.data?.detail || 'Error al registrar entrada'))
    }
  }

  async function salida(id) {
    try {
      const calc = await api.get(`/entradas/calcular/${id}`)
      const valor = calc.data.valor || 0
      if (!confirm(`¿Cobrar $${valor.toLocaleString()}?`)) return

      const { data } = await api.post(`/entradas/salida/${id}`, { metodo_pago: 'efectivo' })
      setMsg(`✅ Salida: ${data.placa} - $${Number(data.valor || 0).toLocaleString()} (cambio: $${Number(data.cambio || 0).toLocaleString()})`)
      cargar()
    } catch (err) {
      setMsg('❌ ' + (err.response?.data?.detail || 'Error al cobrar salida'))
    }
  }

  const filtradas = activas.filter(o =>
    o.placa && o.placa.toLowerCase().includes(buscar.toLowerCase())
  )

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Entradas / Salidas</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      {/* FORMULARIO RESPONSIVE */}
      <form onSubmit={entrada} className="card mb-5 grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
        <div>
          <label className="text-sm font-medium text-slate-600">Placa</label>
          <input className="input w-full" value={form.placa} required placeholder="Ej: ABC123"
            onChange={e => setForm({ ...form, placa: e.target.value.toUpperCase() })} />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-600">Tipo</label>
          <select className="input w-full" value={form.tipo_vehiculo}
            onChange={e => setForm({ ...form, tipo_vehiculo: e.target.value })}>
            <option value="carro">Carro</option>
            <option value="moto">Moto</option>
            <option value="bici">Bicicleta</option>
          </select>
        </div>
        <button className="btn btn-primary flex items-center justify-center gap-2 w-full h-[42px]">
          <Plus size={16} /> Registrar Entrada
        </button>
      </form>

      {/* TABLA RESPONSIVE */}
      <div className="card overflow-hidden">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-3 mb-4">
          <h3 className="font-semibold text-lg">Vehículos dentro ({filtradas.length})</h3>

          <div className="relative w-full md:w-auto">
            <Search className="absolute left-2 top-2.5 text-slate-400" size={16} />
            <input
              type="text"
              placeholder="Buscar placa..."
              className="input pl-8 py-2 w-full md:w-64 text-sm"
              value={buscar}
              onChange={e => setBuscar(e.target.value)}
            />
          </div>
        </div>

        {/* overflow-x-auto permite deslizar la tabla con el dedo en móvil */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm whitespace-nowrap">
            <thead className="text-left text-slate-500 border-b bg-slate-50">
              <tr>
                <th className="py-3 px-2">Ticket</th>
                <th className="px-2">Placa</th>
                <th className="px-2">Tipo</th>
                <th className="px-2">Espacio</th>
                <th className="px-2">Entrada</th>
                <th className="px-2">Acción</th>
              </tr>
            </thead>
            <tbody>
              {Array.isArray(filtradas) && filtradas.map(o => (
                <tr key={o.id} className="border-b hover:bg-slate-50">
                  <td className="py-2 px-2 font-mono text-slate-500">#{o.id}</td>
                  <td className="px-2 font-bold text-blue-600">{o.placa}</td>
                  <td className="px-2 capitalize">{o.tipo_vehiculo}</td>
                  <td className="px-2 font-mono">{o.espacio}</td>
                  <td className="px-2 text-slate-600">{new Date(o.hora_entrada).toLocaleTimeString()}</td>
                  <td className="px-2 py-2">
                    <button onClick={() => salida(o.id)} className="btn btn-danger text-xs flex items-center gap-1">
                      <LogOut size={12} /> Salida
                    </button>
                  </td>
                </tr>
              ))}
              {(!filtradas || filtradas.length === 0) && (
                <tr><td colSpan="6" className="py-8 text-center text-slate-400">No hay vehículos que coincidan</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}