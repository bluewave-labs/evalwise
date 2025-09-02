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
  login: (username: string, password: string, rememberMe?: boolean) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<boolean>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const router = useRouter()

  // Check for existing token on mount and set up refresh interval
  useEffect(() => {
    // Check for existing session via refresh token cookie
    const initializeAuth = async () => {
      try {
        // Try to refresh token to see if we have a valid session
        const refreshed = await refreshToken()
        if (!refreshed) {
          setUser(null)
        }
      } catch (error) {
        console.log('No existing session found')
        setUser(null)
      } finally {
        setLoading(false)
      }
    }
    
    initializeAuth()
    
    // Set up token refresh interval (every 10 minutes)
    const refreshInterval = setInterval(async () => {
      if (user) {
        await refreshToken()
      }
    }, 10 * 60 * 1000) // 10 minutes

    return () => clearInterval(refreshInterval)
  }, [user])
  
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
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: 'POST',
        credentials: 'include'
      })

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
        // Refresh failed, logout user
        await logout()
        return false
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      await logout()
      return false
    }
  }

  const value = {
    user,
    token,
    loading,
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