import { useEffect, useState } from 'react'
import api from '../api'

const hoy = new Date().toISOString().slice(0, 10)

export default function Contabilidad() {
  const [resumen, setResumen] = useState(null)
  const [movs, setMovs] = useState([])
  const [fecha, setFecha] = useState(hoy)
  const [form, setForm] = useState({ tipo: 'egreso', concepto: '', monto: 0, metodo_pago: 'efectivo' })

  const cargar = async () => {
    try {
      const r1 = await api.get(`/contabilidad/resumen?fecha=${fecha}`)
      setResumen(r1.data)

      const r2 = await api.get(`/contabilidad/movimientos?desde=${fecha}&hasta=${fecha}`)
      if (Array.isArray(r2.data)) setMovs(r2.data)
      else setMovs([])
    } catch (err) {
      console.error(err)
      setMovs([])
    }
  }

  useEffect(() => { cargar() }, [fecha])

  async function crear(e) {
    e.preventDefault()
    await api.post('/contabilidad/movimientos', { ...form, monto: +form.monto })
    setForm({ tipo: 'egreso', concepto: '', monto: 0, metodo_pago: 'efectivo' })
    cargar()
  }

  return (
    <div>
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-5 gap-3">
        <h2 className="text-2xl font-bold">Contabilidad</h2>
        <div className="flex items-center gap-2 bg-white px-3 py-1 rounded-lg border shadow-sm w-full md:w-auto">
          <label className="text-sm font-medium text-slate-600">Fecha:</label>
          <input type="date" className="border-none outline-none text-sm bg-transparent flex-1" value={fecha} onChange={e => setFecha(e.target.value)} />
        </div>
      </div>

      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-5">
          <div className="card p-3 md:p-5"><p className="text-xs md:text-sm text-slate-500">Ingresos</p><p className="text-lg md:text-xl font-bold text-green-600">${Number(resumen.ingresos || 0).toLocaleString()}</p></div>
          <div className="card p-3 md:p-5"><p className="text-xs md:text-sm text-slate-500">Egresos</p><p className="text-lg md:text-xl font-bold text-red-600">${Number(resumen.egresos || 0).toLocaleString()}</p></div>
          <div className="card p-3 md:p-5"><p className="text-xs md:text-sm text-slate-500">Neto</p><p className="text-lg md:text-xl font-bold">${Number(resumen.neto || 0).toLocaleString()}</p></div>
          <div className="card p-3 md:p-5"><p className="text-xs md:text-sm text-slate-500">Movs.</p><p className="text-lg md:text-xl font-bold">{resumen.movimientos || 0}</p></div>
        </div>
      )}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-1 md:grid-cols-5 gap-3 items-end">
        <div className="md:col-span-1">
          <label className="text-sm">Tipo</label>
          <select className="input w-full" value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })}>
            <option value="ingreso">Ingreso</option><option value="egreso">Egreso</option>
          </select>
        </div>
        <div className="md:col-span-2">
          <label className="text-sm">Concepto</label>
          <input className="input w-full" placeholder="Ej: Pago aseo" required value={form.concepto} onChange={e => setForm({ ...form, concepto: e.target.value })} />
        </div>
        <div className="md:col-span-1">
          <label className="text-sm">Monto</label>
          <input className="input w-full" type="number" required value={form.monto} onChange={e => setForm({ ...form, monto: e.target.value })} />
        </div>
        <button className="btn btn-primary w-full h-[42px] md:col-span-1">Guardar</button>
      </form>

      <div className="card overflow-hidden">
        <h3 className="font-semibold mb-3">Movimientos del día</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm whitespace-nowrap">
            <thead className="text-left text-slate-500 border-b bg-slate-50">
              <tr><th className="py-2 px-2">Hora</th><th className="px-2">Tipo</th><th className="px-2">Concepto</th><th className="px-2">Monto</th></tr>
            </thead>
            <tbody>
              {Array.isArray(movs) && movs.map(m => (
                <tr key={m.id} className="border-b">
                  <td className="py-2 px-2 text-slate-500">{new Date(m.fecha).toLocaleTimeString()}</td>
                  <td className="px-2"><span className={m.tipo === 'ingreso' ? 'text-green-600 font-bold' : 'text-red-600 font-bold'}>{m.tipo}</span></td>
                  <td className="px-2">{m.concepto}</td>
                  <td className="px-2 font-mono">${Number(m.monto || 0).toLocaleString()}</td>
                </tr>
              ))}
              {(!movs || movs.length === 0) && <tr><td colSpan="4" className="py-6 text-center text-slate-400">Sin movimientos</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}