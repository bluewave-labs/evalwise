"use client"

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { Button } from '@/components/ui'
import { LogOut, User, Settings } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const pathname = usePathname()

  // Don't show navbar on login page
  if (pathname === '/login') {
    return null
  }

  return (
    <nav className="border-b bg-card">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Link href="/">
                <h1 className="text-xl font-bold">EvalWise</h1>
              </Link>
            </div>
            
            {user && (
              <div className="hidden md:block">
                <div className="ml-10 flex items-baseline space-x-4">
                  <Link 
                    href="/" 
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      pathname === '/' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Dashboard
                  </Link>
                  <Link 
                    href="/datasets" 
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      pathname === '/datasets' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Datasets
                  </Link>
                  <Link 
                    href="/scenarios" 
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      pathname === '/scenarios' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Scenarios
                  </Link>
                  <Link 
                    href="/evaluators" 
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      pathname === '/evaluators' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Evaluators
                  </Link>
                  <Link 
                    href="/runs" 
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      pathname === '/runs' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Runs
                  </Link>
                  <Link 
                    href="/playground" 
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      pathname === '/playground' 
                        ? 'bg-primary text-primary-foreground' 
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Playground
                  </Link>
                  {user.is_superuser && (
                    <Link 
                      href="/admin" 
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        pathname === '/admin' 
                          ? 'bg-primary text-primary-foreground' 
                          : 'text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      Admin
                    </Link>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* User menu */}
          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <div className="hidden md:flex items-center space-x-2 text-sm text-muted-foreground">
                  <User className="h-4 w-4" />
                  <span>{user.full_name || user.username}</span>
                  {user.is_superuser && (
                    <span className="px-2 py-1 text-xs bg-primary text-primary-foreground rounded">
                      Admin
                    </span>
                  )}
                </div>
                
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/settings">
                    <Settings className="h-4 w-4" />
                  </Link>
                </Button>
                
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={logout}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <LogOut className="h-4 w-4" />
                  <span className="ml-2 hidden sm:inline">Logout</span>
                </Button>
              </>
            ) : (
              <Button asChild>
                <Link href="/login">Sign In</Link>
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}