import { useEffect, useState } from 'react'
import api from '../api'

const hoy = new Date().toISOString().slice(0, 10)

export default function Contabilidad() {
  const [resumen, setResumen] = useState(null)
  const [movs, setMovs] = useState([])
  const [fecha, setFecha] = useState(hoy)
  const [form, setForm] = useState({ tipo: 'egreso', concepto: '', monto: 0, metodo_pago: 'efectivo' })

  const cargar = async () => {
    const r1 = await api.get(`/contabilidad/resumen?fecha=${fecha}`)
    setResumen(r1.data)
    const r2 = await api.get(`/contabilidad/movimientos?desde=${fecha}&hasta=${fecha}`)
    setMovs(r2.data)
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
      <h2 className="text-2xl font-bold mb-5">Contabilidad</h2>

      <div className="mb-5">
        <label className="text-sm mr-2">Fecha:</label>
        <input type="date" className="input w-auto inline-block" value={fecha} onChange={e => setFecha(e.target.value)} />
      </div>

      {resumen && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
          <div className="card"><p className="text-sm text-slate-500">Ingresos</p><p className="text-xl font-bold text-green-600">${resumen.ingresos.toLocaleString()}</p></div>
          <div className="card"><p className="text-sm text-slate-500">Egresos</p><p className="text-xl font-bold text-red-600">${resumen.egresos.toLocaleString()}</p></div>
          <div className="card"><p className="text-sm text-slate-500">Neto</p><p className="text-xl font-bold">${resumen.neto.toLocaleString()}</p></div>
          <div className="card"><p className="text-sm text-slate-500">Movimientos</p><p className="text-xl font-bold">{resumen.movimientos}</p></div>
        </div>
      )}

      <form onSubmit={crear} className="card mb-5 grid grid-cols-2 md:grid-cols-4 gap-3">
        <select className="input" value={form.tipo} onChange={e => setForm({ ...form, tipo: e.target.value })}>
          <option value="ingreso">Ingreso</option><option value="egreso">Egreso</option>
        </select>
        <input className="input" placeholder="Concepto" required value={form.concepto} onChange={e => setForm({ ...form, concepto: e.target.value })} />
        <input className="input" type="number" placeholder="Monto" required value={form.monto} onChange={e => setForm({ ...form, monto: e.target.value })} />
        <select className="input" value={form.metodo_pago} onChange={e => setForm({ ...form, metodo_pago: e.target.value })}>
          <option value="efectivo">Efectivo</option><option value="tarjeta">Tarjeta</option><option value="transferencia">Transferencia</option>
        </select>
        <button className="btn btn-primary col-span-2 md:col-span-4">Registrar movimiento</button>
      </form>

      <div className="card">
        <h3 className="font-semibold mb-3">Movimientos del día</h3>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Hora</th><th>Tipo</th><th>Concepto</th><th>Monto</th><th>Método</th></tr>
          </thead>
          <tbody>
            {movs.map(m => (
              <tr key={m.id} className="border-b">
                <td className="py-2">{new Date(m.fecha).toLocaleTimeString()}</td>
                <td><span className={m.tipo === 'ingreso' ? 'text-green-600' : 'text-red-600'}>{m.tipo}</span></td>
                <td>{m.concepto}</td>
                <td>${(+m.monto).toLocaleString()}</td>
                <td>{m.metodo_pago}</td>
              </tr>
            ))}
            {!movs.length && <tr><td colSpan="5" className="py-6 text-center text-slate-400">Sin movimientos</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
