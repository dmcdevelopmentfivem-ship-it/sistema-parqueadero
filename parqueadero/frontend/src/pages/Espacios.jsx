import { useEffect, useState } from 'react'
import api from '../api'
import { Trash2 } from 'lucide-react'

export default function Espacios() {
  const [esp, setEsp] = useState([])
  const [form, setForm] = useState({ codigo: '', tipo_vehiculo: 'carro' })
  const [msg, setMsg] = useState('')

  const cargar = () => {
    api.get('/espacios/')
      .then(r => setEsp(Array.isArray(r.data) ? r.data : []))
      .catch(() => setEsp([]))
  }

  useEffect(() => { cargar() }, [])

  async function crear(e) {
    e.preventDefault()
    setMsg('')
    try {
      await api.post('/espacios/', {
        codigo: form.codigo.toUpperCase().trim(),
        tipo_vehiculo: form.tipo_vehiculo
      })
      setForm({ codigo: '', tipo_vehiculo: 'carro' })
      cargar()
      setMsg('✅ Espacio creado correctamente')
    } catch (err) {
      setMsg('❌ ' + (err.response?.data?.detail || 'Error al crear'))
    }
  }

  async function borrar(id, codigo) {
    if (!confirm(`¿Estás seguro de eliminar el espacio ${codigo}?`)) return
    try {
      await api.delete(`/espacios/${id}`)
      cargar()
      setMsg('✅ Espacio eliminado')
    } catch (err) {
      setMsg('❌ ' + (err.response?.data?.detail || 'No se puede borrar'))
    }
  }

  const color = (e) => e.estado === 'libre' ? 'bg-green-100 border-green-400 text-green-700'
    : e.estado === 'ocupado' ? 'bg-red-100 border-red-400 text-red-700'
      : 'bg-slate-100 border-slate-400 text-slate-700'

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Espacios</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      <form onSubmit={crear} className="card mb-5 flex gap-3 items-end flex-wrap">
        <div>
          <label className="text-sm">Código</label>
          <input className="input" required placeholder="Ej: A-01" value={form.codigo}
            onChange={e => setForm({ ...form, codigo: e.target.value.toUpperCase() })} />
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
        <button className="btn btn-primary">Agregar</button>
      </form>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {Array.isArray(esp) && esp.map(e => (
          <div key={e.id} className={`relative border-2 rounded-lg p-3 text-center ${color(e)}`}>
            <button
              onClick={() => borrar(e.id, e.codigo)}
              className="absolute top-1 right-1 text-red-500 hover:text-red-700 bg-white/50 rounded p-1"
              title="Eliminar espacio"
            >
              <Trash2 size={14} />
            </button>
            <p className="font-bold text-lg">{e.codigo}</p>
            <p className="text-xs uppercase">{e.tipo_vehiculo}</p>
            <p className="text-xs mt-1">{e.estado}</p>
          </div>
        ))}
        {(!esp || esp.length === 0) && (
          <p className="col-span-full text-slate-400 p-4">No hay espacios creados en la base de datos.</p>
        )}
      </div>
    </div>
  )
}