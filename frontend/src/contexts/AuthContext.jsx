import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { authApi } from '../api'
import { clearToken, getToken, isAuthenticated, setToken } from '../auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const logout = useCallback(() => {
    clearToken()
    setUser(null)
  }, [])

  const login = useCallback(async (username, password) => {
    const { access_token } = await authApi.login(username, password)
    setToken(access_token)
    const me = await authApi.me()
    setUser(me)
    return me
  }, [])

  useEffect(() => {
    async function restoreSession() {
      if (!isAuthenticated()) {
        setLoading(false)
        return
      }
      try {
        const me = await authApi.me()
        setUser(me)
      } catch {
        clearToken()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    restoreSession()
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAuthenticated: Boolean(user) }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return ctx
}
