import axios, { type AxiosInstance } from 'axios'
import React, { createContext, useContext, useState } from 'react'

interface AuthCtx {
  loggedIn: boolean
  login: (user: string, pass: string) => Promise<void>
  logout: () => void
  api: AxiosInstance
}

const AuthContext = createContext<AuthCtx>(null as unknown as AuthCtx)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loggedIn, setLoggedIn] = useState(false)

  const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '',
    withCredentials: true,
  })

  api.interceptors.response.use(
    (r) => r,
    (error) => {
      if (error.response?.status === 401) setLoggedIn(false)
      return Promise.reject(error)
    },
  )

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
