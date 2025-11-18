"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import ProtectedRoute from '@/components/protected-route'
import { 
  Users, 
  Building2, 
  Activity, 
  AlertTriangle, 
  Shield,
  Search,
  Plus,
  Edit,
  Trash2,
  Eye,
  EyeOff,
  RefreshCw
} from "lucide-react"
import { useAuth } from '@/contexts/auth-context'
import CreateUserModal from '@/components/create-user-modal'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AdminStats {
  total_users: number
  active_users: number
  total_organizations: number
  active_organizations: number
  recent_logins: number
  failed_logins_24h: number
  active_sessions: number
}

interface User {
  id: string
  email: string
  username: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
  last_login: string | null
  rate_limit_tier: string
}

interface NewUser {
  email: string
  username: string
  password: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  rate_limit_tier: string
}

function AdminPageContent() {
  const { user, token } = useAuth()
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [showCreateUserModal, setShowCreateUserModal] = useState(false)
  const [showPasswords, setShowPasswords] = useState(false)
  const [createUserLoading, setCreateUserLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (err) {
      console.error('Failed to fetch admin stats:', err)
    }
  }

  const fetchUsers = async () => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/admin/users?limit=50${searchTerm ? `&search=${encodeURIComponent(searchTerm)}` : ''}`, 
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setUsers(data)
      }
    } catch (err) {
      console.error('Failed to fetch users:', err)
    }
  }

  const createUser = async (userData: NewUser) => {
    setError('')
    setCreateUserLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({...userData, rate_limit_tier: 'basic'})
      })

      if (response.ok) {
        await fetchUsers()
        await fetchStats()
        setShowCreateUserModal(false)
      } else {
        const errorData = await response.json()
        setError(errorData.detail?.message || 'Failed to create user')
        throw new Error(errorData.detail?.message || 'Failed to create user')
      }
    } catch (err) {
      const errorMessage = 'Network error occurred'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setCreateUserLoading(false)
    }
  }

  const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: !currentStatus })
      })

      if (response.ok) {
        await fetchUsers()
        await fetchStats()
      }
    } catch (err) {
      console.error('Failed to toggle user status:', err)
    }
  }

  useEffect(() => {
    if (user?.is_superuser && token) {
      fetchStats()
      fetchUsers()
      setLoading(false)
    }
  }, [user, token])

  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (token) {
        fetchUsers()
      }
    }, 500)

    return () => clearTimeout(delayedSearch)
  }, [searchTerm, token])

  if (!user?.is_superuser) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="w-full max-w-md text-center">
          <CardHeader>
            <Shield className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <CardTitle>Admin Access Required</CardTitle>
            <CardDescription>
              You need administrator privileges to access this page.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <RefreshCw className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-muted-foreground">
          Manage users, organizations, and system settings
        </p>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Users</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_users}</div>
              <p className="text-xs text-muted-foreground">
                {stats.active_users} active users
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Organizations</CardTitle>
              <Building2 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_organizations}</div>
              <p className="text-xs text-muted-foreground">
                {stats.active_organizations} active orgs
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Recent Logins</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.recent_logins}</div>
              <p className="text-xs text-muted-foreground">
                Last 24 hours
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Failed Logins</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.failed_logins_24h}</div>
              <p className="text-xs text-muted-foreground">
                {stats.active_sessions} active sessions
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* User Management */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>User Management</CardTitle>
              <CardDescription>
                Manage system users and their permissions
              </CardDescription>
            </div>
            <Button onClick={() => setShowCreateUserModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create User
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search */}
          <div className="flex items-center space-x-2">
            <Search className="w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search users by username, email, or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="max-w-sm"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowPasswords(!showPasswords)}
            >
              {showPasswords ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </Button>
          </div>


          {/* Users Table */}
          <div className="border rounded-md">
            <div className="grid grid-cols-6 gap-4 p-4 border-b bg-muted/50 font-medium text-sm">
              <div>User</div>
              <div>Email</div>
              <div>Status</div>
              <div>Role</div>
              <div>Created</div>
              <div>Actions</div>
            </div>
            {users.map((user) => (
              <div key={user.id} className="grid grid-cols-6 gap-4 p-4 border-b">
                <div>
                  <div className="font-medium">{user.username}</div>
                  {user.full_name && (
                    <div className="text-sm text-muted-foreground">{user.full_name}</div>
                  )}
                </div>
                <div className="text-sm">{user.email}</div>
                <div>
                  <Badge variant={user.is_active ? "default" : "secondary"}>
                    {user.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
                <div>
                  <div className="flex space-x-1">
                    {user.is_superuser && (
                      <Badge variant="destructive">Admin</Badge>
                    )}
                    <Badge variant="outline">{user.rate_limit_tier}</Badge>
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  {new Date(user.created_at).toLocaleDateString()}
                </div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toggleUserStatus(user.id, user.is_active)}
                  >
                    {user.is_active ? "Deactivate" : "Activate"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Create User Modal */}
      <CreateUserModal
        isOpen={showCreateUserModal}
        onClose={() => {
          setShowCreateUserModal(false)
          setError('')
        }}
        onSubmit={createUser}
        isLoading={createUserLoading}
        error={error}
      />
    </div>
  )
}

export default function AdminPage() {
  return (
    <ProtectedRoute requireAdmin={true}>
      <AdminPageContent />
    </ProtectedRoute>
  )
}