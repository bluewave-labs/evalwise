"use client"

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
  redirectTo?: string
}

export default function ProtectedRoute({ 
  children, 
  requireAdmin = false, 
  redirectTo = '/login' 
}: ProtectedRouteProps) {
  const { user, loading } = useAuth()
  const router = useRouter()

  const pathname = usePathname()

  useEffect(() => {
    if (!loading) {
      if (!user) {
        // Use URL parameter instead of localStorage for better UX
        const returnTo = encodeURIComponent(pathname || '/')
        router.push(`${redirectTo}?returnTo=${returnTo}`)
        return
      }

      if (requireAdmin && !user.is_superuser) {
        router.push('/') // Redirect to dashboard if not admin
        return
      }
    }
  }, [user, loading, requireAdmin, router, redirectTo, pathname])

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary"></div>
      </div>
    )
  }

  // Don't render children until we've confirmed authentication
  if (!user) {
    return null
  }

  if (requireAdmin && !user.is_superuser) {
    return null
  }

  return <>{children}</>
}