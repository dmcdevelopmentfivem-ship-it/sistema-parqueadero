import { useEffect, useState } from 'react'
import api from '../api'
import { Trash2, Edit2, Check, X } from 'lucide-react'

export default function Espacios() {
  const [esp, setEsp] = useState([])
  const [form, setForm] = useState({ codigo: '', tipo_vehiculo: 'carro' })
  const [msg, setMsg] = useState('')

  const [editandoId, setEditandoId] = useState(null)
  const [editForm, setEditForm] = useState({ codigo: '', tipo_vehiculo: '' })

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
      setMsg('✅ Espacio eliminado del mapa')
    } catch (err) {
      setMsg('❌ ' + (err.response?.data?.detail || 'No se puede borrar'))
    }
  }

  const iniciarEdicion = (e) => {
    setEditandoId(e.id)
    setEditForm({ codigo: e.codigo, tipo_vehiculo: e.tipo_vehiculo })
  }

  const cancelarEdicion = () => {
    setEditandoId(null)
    setEditForm({ codigo: '', tipo_vehiculo: '' })
  }

  const guardarEdicion = async (id) => {
    try {
      await api.put(`/espacios/${id}`, {
        codigo: editForm.codigo.toUpperCase().trim(),
        tipo_vehiculo: editForm.tipo_vehiculo
      })
      setEditandoId(null)
      cargar()
      setMsg('✅ Espacio actualizado correctamente')
    } catch (err) {
      setMsg('❌ ' + (err.response?.data?.detail || 'Error al editar'))
    }
  }

  const color = (e) => e.estado === 'libre' ? 'bg-green-100 border-green-400 text-green-700'
    : e.estado === 'ocupado' ? 'bg-red-100 border-red-400 text-red-700'
      : 'bg-slate-100 border-slate-400 text-slate-700'

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Espacios</h2>
      {msg && <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded text-sm">{msg}</div>}

      {/* FORMULARIO RESPONSIVE */}
      <form onSubmit={crear} className="card mb-5 grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
        <div>
          <label className="text-sm font-medium text-slate-600">Código</label>
          <input className="input w-full" required placeholder="Ej: A-01" value={form.codigo}
            onChange={e => setForm({ ...form, codigo: e.target.value.toUpperCase() })} />
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
        <button className="btn btn-primary w-full h-[42px]">Agregar Espacio</button>
      </form>

      {/* CUADRÍCULA RESPONSIVE (2 col en cel, hasta 6 en PC) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {Array.isArray(esp) && esp.map(e => (
          <div key={e.id} className={`relative border-2 rounded-xl p-3 text-center transition-all ${color(e)}`}>

            {editandoId === e.id ? (
              <div className="flex flex-col gap-2">
                <input
                  className="input text-center px-1 py-1 text-sm w-full font-bold"
                  value={editForm.codigo}
                  onChange={ev => setEditForm({ ...editForm, codigo: ev.target.value.toUpperCase() })}
                  autoFocus
                />
                <select
                  className="input text-center px-1 py-1 text-xs w-full"
                  value={editForm.tipo_vehiculo}
                  onChange={ev => setEditForm({ ...editForm, tipo_vehiculo: ev.target.value })}
                >
                  <option value="carro">Carro</option>
                  <option value="moto">Moto</option>
                  <option value="bici">Bici</option>
                </select>
                <div className="flex justify-center gap-2 mt-1">
                  <button onClick={() => guardarEdicion(e.id)} className="text-green-700 hover:bg-green-200 p-1.5 rounded bg-white/70 shadow-sm" title="Guardar">
                    <Check size={16} />
                  </button>
                  <button onClick={cancelarEdicion} className="text-slate-600 hover:bg-slate-200 p-1.5 rounded bg-white/70 shadow-sm" title="Cancelar">
                    <X size={16} />
                  </button>
                </div>
              </div>
            ) : (
              <>
                <div className="absolute top-1 right-1 flex gap-1">
                  <button
                    onClick={() => iniciarEdicion(e)}
                    className="text-blue-600 hover:text-blue-800 bg-white/60 rounded p-1.5 shadow-sm"
                    title="Editar"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    onClick={() => borrar(e.id, e.codigo)}
                    className="text-red-500 hover:text-red-700 bg-white/60 rounded p-1.5 shadow-sm"
                    title="Eliminar"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                <p className="font-bold text-xl mt-3">{e.codigo}</p>
                <p className="text-xs uppercase font-semibold opacity-80">{e.tipo_vehiculo}</p>
                <p className="text-xs mt-2 font-bold bg-white/50 inline-block px-2 py-0.5 rounded-full">{e.estado}</p>
              </>
            )}

          </div>
        ))}
        {(!esp || esp.length === 0) && (
          <p className="col-span-full text-slate-400 p-4 text-center">No hay espacios creados en la base de datos.</p>
        )}
      </div>
    </div>
  )
}