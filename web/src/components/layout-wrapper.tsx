'use client'

import { usePathname } from 'next/navigation'
import Sidebar from '@/components/sidebar'

interface LayoutWrapperProps {
  children: React.ReactNode
}

export default function LayoutWrapper({ children }: LayoutWrapperProps) {
  const pathname = usePathname()
  
  // Auth pages that shouldn't show sidebar
  const isAuthPage = !pathname || 
    pathname === '/login' || 
    pathname === '/forgot-password' || 
    pathname.startsWith('/reset-password')

  if (isAuthPage) {
    return (
      <div className="min-h-screen">
        <main className="p-6">
          {children}
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <Sidebar />
      <main className="ml-64 p-6 sidebar-main">
        {children}
      </main>
    </div>
  )
}