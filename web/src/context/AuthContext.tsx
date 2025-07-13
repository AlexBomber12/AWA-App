import type { AxiosInstance } from 'axios'
import React, { createContext, useContext, useState } from 'react'
import { api } from '../lib/api'

interface AuthCtx {
  loggedIn: boolean
  login: (user: string, pass: string) => Promise<void>
  logout: () => void
  api: AxiosInstance
}

const AuthContext = createContext<AuthCtx>(null as unknown as AuthCtx)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loggedIn, setLoggedIn] = useState(false)

  api.interceptors.response.use(
    (r) => r,
    (error) => {
      if (error.response?.status === 401) setLoggedIn(false)
      return Promise.reject(error)
    },
  )
  api.interceptors.request.use((config) => {
    const m = document.cookie.match(/access_token=([^;]+)/)
    if (m) config.headers.Authorization = `Bearer ${m[1]}`
    return config
  })

  const login = async (username: string, password: string) => {
    await api.post('/auth/token', { username, password })
    setLoggedIn(true)
  }

  const logout = () => {
    setLoggedIn(false)
  }

  return <AuthContext.Provider value={{ loggedIn, login, logout, api }}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
