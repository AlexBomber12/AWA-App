import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const [username, setUser] = useState('')
  const [password, setPass] = useState('')
  const navigate = useNavigate()
  const { login } = useAuth()
  return (
    <div className="flex items-center justify-center h-screen bg-gray-100">
      <form
        className="p-4 bg-white rounded shadow space-y-2"
        onSubmit={async (e) => {
          e.preventDefault()
          await login(username, password)
          navigate('/dashboard')
        }}
      >
        <input
          className="border p-2 w-full"
          placeholder="Username"
          value={username}
          onChange={(e) => setUser(e.target.value)}
        />
        <input
          className="border p-2 w-full"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPass(e.target.value)}
        />
        <button className="bg-blue-600 text-white px-4 py-2 rounded w-full" type="submit">
          Login
        </button>
      </form>
    </div>
  )
}
