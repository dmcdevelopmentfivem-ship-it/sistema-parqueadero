import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../auth'

export default function Login() {
  const [email, setEmail] = useState('admin@parqueadero.com')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const nav = useNavigate()

  async function submit(e) {
    e.preventDefault()
    setError('')
    try {
      const form = new URLSearchParams()
      form.append('username', email)
      form.append('password', password)
      const { data } = await api.post('/auth/login', form)

      // 1. Guardamos el token y el usuario en el contexto y en el localStorage
      login(data)

      // 2. Usamos window.location.href en lugar de navigate() 
      // Esto fuerza una recarga completa de la página y evita el bug de React Router en Render
      window.location.href = '/'

    } catch (err) {
      setError(err.response?.data?.detail || 'Error de login')
    }
  }
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900">
      <form onSubmit={submit} className="bg-white p-8 rounded-xl shadow-xl w-96">
        <h1 className="text-2xl font-bold text-center mb-1">🅿️ Parqueadero</h1>
        <p className="text-center text-slate-500 text-sm mb-6">Ingresa a tu cuenta</p>
        {error && <div className="bg-red-100 text-red-700 p-2 rounded mb-3 text-sm">{error}</div>}
        <label className="block text-sm mb-1">Email</label>
        <input className="input mb-3" value={email} onChange={e => setEmail(e.target.value)} />
        <label className="block text-sm mb-1">Contraseña</label>
        <input type="password" className="input mb-4" value={password} onChange={e => setPassword(e.target.value)} />
        <button className="btn btn-primary w-full">Ingresar</button>
        <p className="text-xs text-slate-400 text-center mt-4">
          Demo: admin@parqueadero.com / admin123
        </p>
      </form>
    </div>
  )
}
