'use client'

import { useState, useEffect } from 'react'
import { Settings, Building2, Users, Shield, Key } from 'lucide-react'
import { useAuth } from '@/contexts/auth-context'
import { api } from '@/lib/api'
import ProtectedRoute from '@/components/protected-route'

interface Organization {
  id: string
  name: string
  description?: string
  created_at: string
  member_count?: number
  role?: string
}

export default function SettingsPage() {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('organization')
  const [organizations, setOrganizations] = useState<Organization[]>([])
  const [editingOrg, setEditingOrg] = useState<Organization | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadOrganizations()
  }, [user])

  const loadOrganizations = async () => {
    if (!user) return
    
    try {
      // Use user's organizations for now
      const userOrgs = user.organizations.map(org => ({
        id: org.id,
        name: org.name,
        role: org.role,
        created_at: new Date().toISOString(),
        member_count: 1
      }))
      setOrganizations(userOrgs)
    } catch (error) {
      console.error('Failed to load organizations:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateOrganization = async (orgId: string, updates: Partial<Organization>) => {
    try {
      await api.patch(`/organizations/${orgId}`, updates)
      await loadOrganizations()
      setEditingOrg(null)
      alert('Organization updated successfully')
    } catch (error) {
      console.error('Failed to update organization:', error)
      alert('Failed to update organization')
    }
  }

  const tabs = [
    { id: 'organization', label: 'Organization', icon: Building2 },
    { id: 'team', label: 'Team Members', icon: Users },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'api-keys', label: 'API Keys', icon: Key }
  ]

  return (
    <ProtectedRoute>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center space-x-2">
            <Settings className="h-8 w-8" />
            <span>Settings</span>
          </h1>
          <p className="text-gray-600 mt-1">Manage your organization and account settings</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 pb-3 px-1 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-500'
                      : 'border-transparent text-gray-600 hover:text-gray-800'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          {activeTab === 'organization' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Organization Settings</h2>
              
              {loading ? (
                <p className="text-gray-600">Loading organizations...</p>
              ) : organizations.length === 0 ? (
                <div className="bg-gray-50 rounded-lg p-8 text-center">
                  <Building2 className="h-12 w-12 text-gray-500 mx-auto mb-3" />
                  <p className="text-gray-600">No organizations found</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {organizations.map(org => (
                    <div key={org.id} className="bg-gray-50 rounded-lg p-4">
                      {editingOrg?.id === org.id ? (
                        <div className="space-y-4">
                          <input
                            type="text"
                            value={editingOrg.name}
                            onChange={(e) => setEditingOrg({ ...editingOrg, name: e.target.value })}
                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                          />
                          <textarea
                            value={editingOrg.description || ''}
                            onChange={(e) => setEditingOrg({ ...editingOrg, description: e.target.value })}
                            placeholder="Organization description"
                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                            rows={3}
                          />
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleUpdateOrganization(org.id, {
                                name: editingOrg.name,
                                description: editingOrg.description
                              })}
                              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => setEditingOrg(null)}
                              className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex justify-between items-start">
                          <div>
                            <h3 className="text-lg font-medium text-gray-900">{org.name}</h3>
                            <p className="text-gray-600 text-sm mt-1">{org.description || 'No description'}</p>
                            <div className="flex items-center space-x-4 mt-2 text-sm text-gray-600">
                              <span>Role: {org.role}</span>
                              <span>Members: {org.member_count || 1}</span>
                            </div>
                          </div>
                          <button
                            onClick={() => setEditingOrg(org)}
                            className="bg-gray-600 hover:bg-gray-500 text-white px-3 py-1 rounded text-sm"
                          >
                            Edit
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="mt-6 pt-6 border-t border-gray-200">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Organization</h3>
                <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
                  Create Organization
                </button>
              </div>
            </div>
          )}

          {activeTab === 'team' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Team Members</h2>
              <p className="text-gray-600">Manage team members and permissions</p>
              
              <div className="bg-gray-50 rounded-lg p-8 text-center">
                <Users className="h-12 w-12 text-gray-500 mx-auto mb-3" />
                <p className="text-gray-600">Team management coming soon</p>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">Security Settings</h2>
              
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-2">Password</h3>
                  <p className="text-gray-600 text-sm mb-3">Last changed: Never</p>
                  <button className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded text-sm">
                    Change Password
                  </button>
                </div>
              </div>
            </div>
          )}


          {activeTab === 'api-keys' && (
            <div className="space-y-6">
              <h2 className="text-xl font-semibold text-gray-900">API Keys</h2>
              <p className="text-gray-600">Manage API keys for programmatic access</p>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800 text-sm">
                  <strong>Note:</strong> Store your API keys securely. They provide full access to your account.
                </p>
              </div>
              
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
                Generate New API Key
              </button>
            </div>
          )}
        </div>
      </div>
    </ProtectedRoute>
  )
}