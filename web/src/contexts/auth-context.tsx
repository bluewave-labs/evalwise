"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

interface User {
  id: string
  username: string
  email: string
  full_name?: string
  is_superuser: boolean
  organizations: Array<{
    id: string
    name: string
    role: string
  }>
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string, rememberMe?: boolean) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<boolean>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [hydrated, setHydrated] = useState(false)
  const router = useRouter()

  // Restore from sessionStorage after hydration to avoid mismatch
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const cachedUser = sessionStorage.getItem('auth_user')
      const cachedToken = sessionStorage.getItem('auth_token')

      if (cachedUser) {
        try {
          setUser(JSON.parse(cachedUser))
        } catch {
          // Invalid cached data, ignore
        }
      }

      if (cachedToken) {
        setToken(cachedToken)
        ;(window as any).__authToken = cachedToken
      }

      setHydrated(true)
    }
  }, [])

  // Persist user and token to sessionStorage when they change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (user) {
        sessionStorage.setItem('auth_user', JSON.stringify(user))
      } else {
        sessionStorage.removeItem('auth_user')
      }
    }
  }, [user])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      if (token) {
        sessionStorage.setItem('auth_token', token)
        ;(window as any).__authToken = token
      } else {
        sessionStorage.removeItem('auth_token')
        ;(window as any).__authToken = null
      }
    }
  }, [token])

  // Check for existing token after hydration
  useEffect(() => {
    // Wait for hydration to complete before checking auth
    if (!hydrated) return

    // Check for existing session via refresh token cookie
    const initializeAuth = async () => {
      // If we have cached user/token, validate it quickly
      if (user && token) {
        console.log('Using cached auth state')
        setLoading(false)
        return
      }

      try {
        console.log('Initializing auth with API_BASE_URL:', API_BASE_URL)
        // Try to refresh token to see if we have a valid session
        const refreshed = await refreshToken()
        console.log('Token refresh result:', refreshed)
        if (!refreshed) {
          console.log('No valid session, setting user to null')
          setUser(null)
        }
      } catch (error) {
        console.error('Error during auth initialization:', error)
        setUser(null)
      } finally {
        console.log('Auth initialization complete, setting loading to false')
        setLoading(false)
      }
    }

    initializeAuth()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated]) // Run after hydration completes

  // Set up token refresh interval in a separate effect
  useEffect(() => {
    if (!user) return

    // Set up token refresh interval (every 10 minutes)
    const refreshInterval = setInterval(async () => {
      await refreshToken()
    }, 10 * 60 * 1000) // 10 minutes

    return () => clearInterval(refreshInterval)
  }, [user?.id]) // Only depend on user ID to avoid unnecessary re-runs
  
  // Token managed via secure httpOnly cookies - no global window token needed

  const checkAuth = async () => {
    try {
      // Use token if available, otherwise rely on cookie-based authentication
      const headers: HeadersInit = {
        'Content-Type': 'application/json'
      }
      
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }
      
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        credentials: 'include', // Include cookies for authentication
        headers
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Try to refresh token if available
        const refreshed = await refreshToken()
        if (!refreshed) {
          setUser(null)
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string, rememberMe: boolean = false) => {
    setLoading(true)
    
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        credentials: 'include', // Include cookies for refresh token
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: new URLSearchParams({
          username,
          password,
          remember_me: rememberMe.toString()
        })
      })

      if (!response.ok) {
        console.log('Login response status:', response.status)
        const error = await response.json()
        console.log('Login error response:', error)
        throw new Error(error.detail || 'Login failed')
      }

      const data = await response.json()
      console.log('Login response data:', data)
      console.log('Access token:', data.access_token)
      
      // Store access token in memory (React state/context)
      // Refresh token is automatically stored in httpOnly cookie by backend
      
      // Get user data
      const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
          'Content-Type': 'application/json'
        }
      })

      if (userResponse.ok) {
        const userData = await userResponse.json()
        setUser(userData)
        
        // Store access token in memory only - refresh token handled via httpOnly cookie
        setToken(data.access_token)
        
        // Set global token for API client
        if (typeof window !== 'undefined') {
          (window as any).__authToken = data.access_token
        }
        
        // Small delay to ensure state is set before navigation
        setTimeout(() => {
          router.push('/')
        }, 100)
      } else {
        throw new Error('Failed to get user data')
      }
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      })
    } catch (error) {
      console.error('Logout request failed:', error)
    }

    // Clear local state - cookies handled by server
    setUser(null)
    setToken(null)
    
    // Clear global token for API client
    if (typeof window !== 'undefined') {
      (window as any).__authToken = null
    }
    
    // Redirect to login
    router.push('/login')
  }

  const refreshToken = async (): Promise<boolean> => {
    try {
      console.log('Attempting token refresh at:', `${API_BASE_URL}/auth/refresh`)
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include'
      })
      console.log('Refresh response status:', response.status, response.statusText)

      if (response.ok) {
        const data = await response.json()
        setToken(data.access_token)

        // Set global token for API client
        if (typeof window !== 'undefined') {
          (window as any).__authToken = data.access_token
        }

        // Get fresh user data if we don't have it
        if (!user) {
          try {
            const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
              method: 'GET',
              credentials: 'include',
              headers: {
                'Authorization': `Bearer ${data.access_token}`,
                'Content-Type': 'application/json'
              }
            })

            if (userResponse.ok) {
              const userData = await userResponse.json()
              setUser(userData)
            }
          } catch (userError) {
            console.error('Failed to get user data after refresh:', userError)
          }
        }

        return true
      } else {
        // Refresh failed, clear state but don't call logout to avoid redirect loops
        setUser(null)
        setToken(null)
        if (typeof window !== 'undefined') {
          (window as any).__authToken = null
        }
        return false
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      // Clear state but don't call logout to avoid redirect loops
      setUser(null)
      setToken(null)
      if (typeof window !== 'undefined') {
        (window as any).__authToken = null
      }
      return false
    }
  }

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshToken
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}