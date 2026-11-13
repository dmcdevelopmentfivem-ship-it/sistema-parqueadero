import { useEffect, useState } from 'react'
import api from '../api'

const hoy = new Date().toISOString().slice(0, 10)
const hace30 = new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)

export default function Reportes() {
  const [desde, setDesde] = useState(hace30)
  const [hasta, setHasta] = useState(hoy)
  const [historial, setHistorial] = useState([])

  useEffect(() => {
    api.get(`/reportes/historial?desde=${desde}&hasta=${hasta}`)
      .then(r => {
        // PROTECCIÓN: Validamos que sea una lista antes de guardarla
        if (Array.isArray(r.data)) {
          setHistorial(r.data)
        } else {
          setHistorial([])
        }
      })
      .catch(err => {
        console.error(err)
        setHistorial([]) // Si falla la petición, ponemos lista vacía
      })
  }, [desde, hasta])

  return (
    <div>
      <h2 className="text-2xl font-bold mb-5">Reportes</h2>

      <div className="card mb-5 flex gap-3 items-end flex-wrap">
        <div><label className="text-sm">Desde</label><input type="date" className="input" value={desde} onChange={e => setDesde(e.target.value)} /></div>
        <div><label className="text-sm">Hasta</label><input type="date" className="input" value={hasta} onChange={e => setHasta(e.target.value)} /></div>
      </div>

      <div className="card overflow-x-auto">
        <h3 className="font-semibold mb-3">Historial de ocupaciones ({Array.isArray(historial) ? historial.length : 0})</h3>
        <table className="w-full text-sm">
          <thead className="text-left text-slate-500 border-b">
            <tr><th className="py-2">Placa</th><th>Tipo</th><th>Entrada</th><th>Salida</th><th>Min</th><th>Valor</th><th>Estado</th></tr>
          </thead>
          <tbody>
            {/* PROTECCIÓN: Validamos que historial sea un array antes del .map */}
            {Array.isArray(historial) && historial.map(h => (
              <tr key={h.id} className="border-b">
                <td className="py-2 font-bold">{h.placa}</td><td>{h.tipo}</td>
                <td>{h.entrada ? new Date(h.entrada).toLocaleString() : '-'}</td>
                <td>{h.salida ? new Date(h.salida).toLocaleString() : '-'}</td>
                <td>{h.minutos ?? '-'}</td>
                <td>${Number(h.valor || 0).toLocaleString()}</td>
                <td>{h.estado}</td>
              </tr>
            ))}
            {(!historial || historial.length === 0) && <tr><td colSpan="7" className="py-6 text-center text-slate-400">Sin datos</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}