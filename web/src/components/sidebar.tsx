"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { Button } from '@/components/ui'
import { 
  LayoutDashboard, 
  Database, 
  FileText, 
  TestTube, 
  Play, 
  Beaker, 
  Settings, 
  LogOut, 
  User, 
  Shield,
  ChevronLeft,
  ChevronRight,
  Key
} from 'lucide-react'
import { useState } from 'react'

const navigationItems = [
  {
    name: 'Dashboard',
    href: '/',
    icon: LayoutDashboard
  },
  {
    name: 'Datasets',
    href: '/datasets',
    icon: Database
  },
  {
    name: 'Scenarios',
    href: '/scenarios',
    icon: FileText
  },
  {
    name: 'Evaluators',
    href: '/evaluators',
    icon: TestTube
  },
  {
    name: 'Runs',
    href: '/runs',
    icon: Play
  },
  {
    name: 'Providers',
    href: '/providers',
    icon: Key
  },
  {
    name: 'Playground',
    href: '/playground',
    icon: Beaker
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings
  }
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)

  // Don't show sidebar on auth pages
  if (!pathname || pathname === '/login' || pathname === '/forgot-password' || pathname.startsWith('/reset-password')) {
    return null
  }

  if (!user) {
    return null
  }

  const sidebarWidth = collapsed ? 'w-16' : 'w-64'

  return (
    <div className={`${sidebarWidth} transition-all duration-300 bg-white border-r border-gray-200 min-h-screen flex flex-col`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <Link href="/">
              <h1 className="text-xl font-bold text-gray-900">EvalWise</h1>
            </Link>
          )}
          <Button 
            variant="ghost" 
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="h-8 w-8 p-0"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2">
        <ul className="space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            
            return (
              <li key={item.name}>
                <Link 
                  href={item.href}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors group ${
                    isActive
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                  title={collapsed ? item.name : undefined}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  {!collapsed && (
                    <span className="ml-3">{item.name}</span>
                  )}
                </Link>
              </li>
            )
          })}
          
          {/* Admin Section */}
          {user.is_superuser && (
            <>
              <li className="pt-4">
                {!collapsed && (
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Admin
                  </div>
                )}
              </li>
              <li>
                <Link 
                  href="/admin"
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors group ${
                    pathname === '/admin'
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                  title={collapsed ? 'Admin' : undefined}
                >
                  <Shield className="h-5 w-5 flex-shrink-0" />
                  {!collapsed && (
                    <span className="ml-3">Admin Panel</span>
                  )}
                </Link>
              </li>
            </>
          )}
        </ul>
      </nav>

      {/* User section */}
      <div className="border-t border-gray-200 p-4">
        {/* User info */}
        {!collapsed && (
          <div className="mb-3 px-2">
            <div className="flex items-center space-x-2 text-sm">
              <User className="h-4 w-4 text-gray-500" />
              <div className="flex-1 min-w-0">
                <div className="truncate font-medium text-gray-900">
                  {user.full_name || user.username}
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500 truncate">
                    {user.email}
                  </span>
                  {user.is_superuser && (
                    <span className="px-1.5 py-0.5 text-xs bg-blue-600 text-white rounded">
                      Admin
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="space-y-1">
          <Link 
            href="/settings"
            className={`flex items-center w-full px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              pathname === '/settings'
                ? 'bg-blue-600 text-white' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
            title={collapsed ? 'Settings' : undefined}
          >
            <Settings className="h-4 w-4 flex-shrink-0" />
            {!collapsed && (
              <span className="ml-3">Settings</span>
            )}
          </Link>
          
          <Button 
            variant="ghost" 
            size="sm"
            onClick={logout}
            className={`flex items-center w-full justify-start px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 ${
              collapsed ? 'px-2' : ''
            }`}
            title={collapsed ? 'Logout' : undefined}
          >
            <LogOut className="h-4 w-4 flex-shrink-0" />
            {!collapsed && (
              <span className="ml-3">Logout</span>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}