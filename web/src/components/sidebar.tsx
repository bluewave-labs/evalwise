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
  ChevronDown,
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
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  // Don't show sidebar on auth pages
  if (!pathname || pathname === '/login' || pathname === '/forgot-password' || pathname.startsWith('/reset-password')) {
    return null
  }

  if (!user) {
    return null
  }

  const sidebarWidth = collapsed ? 'w-16' : 'w-64'

  return (
    <div className={`${sidebarWidth} transition-all duration-300 bg-white border-r border-gray-200 h-screen flex flex-col fixed top-0 left-0 z-10`}>
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
        {/* User dropdown trigger */}
        {!collapsed && (
          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            >
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4 text-gray-500" />
                <div className="truncate">
                  {user.full_name || user.username}
                </div>
              </div>
              <ChevronDown className={`h-4 w-4 text-gray-500 transition-transform ${
                userMenuOpen ? 'transform rotate-180' : ''
              }`} />
            </button>

            {/* Dropdown menu */}
            {userMenuOpen && (
              <div className="absolute bottom-full left-0 right-0 mb-1 bg-white border border-gray-200 rounded-md shadow-lg py-1">
                <Link 
                  href="/settings"
                  className={`flex items-center w-full px-3 py-2 text-sm font-medium transition-colors ${
                    pathname === '/settings'
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                  onClick={() => setUserMenuOpen(false)}
                >
                  <Settings className="h-4 w-4 flex-shrink-0" />
                  <span className="ml-3">Settings</span>
                </Link>
                
                <button
                  onClick={() => {
                    setUserMenuOpen(false)
                    logout()
                  }}
                  className="flex items-center w-full px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                >
                  <LogOut className="h-4 w-4 flex-shrink-0" />
                  <span className="ml-3">Logout</span>
                </button>
              </div>
            )}
          </div>
        )}

        {/* Collapsed state - show icon only */}
        {collapsed && (
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="w-full flex items-center justify-center p-2 text-gray-500 hover:bg-gray-100 rounded-md transition-colors"
            title={user.full_name || user.username}
          >
            <User className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}