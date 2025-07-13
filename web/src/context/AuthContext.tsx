import axios, { type AxiosInstance } from 'axios'
import React, { createContext, useContext, useState } from 'react'

interface AuthCtx {
  token: string | null
  login: (user: string, pass: string) => Promise<void>
  logout: () => void
  api: AxiosInstance
}

const AuthContext = createContext<AuthCtx>(null as unknown as AuthCtx)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))

  const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',
    withCredentials: true,
  })

  api.interceptors.request.use((config) => {
    if (token) {
      config.headers = config.headers || {}
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  })

  const login = async (username: string, password: string) => {
    const res = await api.post('/auth/token', { username, password })
    const tok: string = res.data.access_token
    setToken(tok)
    localStorage.setItem('token', tok)
  }

  const logout = () => {
    setToken(null)
    localStorage.removeItem('token')
  }

  return <AuthContext.Provider value={{ token, login, logout, api }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
