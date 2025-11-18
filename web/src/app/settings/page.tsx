'use client'

import { useState, useEffect } from 'react'
import { Settings, Building2, Users, Shield, Plus } from 'lucide-react'
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
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [apiKeyForm, setApiKeyForm] = useState({
    name: '',
    description: ''
  })
  const [apiKeyLoading, setApiKeyLoading] = useState(false)
  const [members, setMembers] = useState<any[]>([])
  const [membersLoading, setMembersLoading] = useState(false)
  const [inviteForm, setInviteForm] = useState({
    email: '',
    role: 'member'
  })
  const [inviteLoading, setInviteLoading] = useState(false)
  const [createUserForm, setCreateUserForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    role: 'member'
  })
  const [createUserLoading, setCreateUserLoading] = useState(false)
  const [showCreateUserForm, setShowCreateUserForm] = useState(false)

  useEffect(() => {
    loadOrganizations()
  }, [user])

  useEffect(() => {
    if (activeTab === 'team' && organizations.length > 0) {
      loadMembers()
    }
  }, [activeTab, organizations])

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

  const handleChangePassword = async () => {
    if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      alert('New passwords do not match')
      return
    }
    
    if (passwordForm.newPassword.length < 8) {
      alert('New password must be at least 8 characters long')
      return
    }
    
    setPasswordLoading(true)
    try {
      await api.patch('/users/me/password', {
        current_password: passwordForm.currentPassword,
        new_password: passwordForm.newPassword
      })
      setPasswordForm({ currentPassword: '', newPassword: '', confirmPassword: '' })
      alert('Password changed successfully')
    } catch (error: any) {
      console.error('Failed to change password:', error)
      const message = error.response?.data?.detail || 'Failed to change password'
      alert(message)
    } finally {
      setPasswordLoading(false)
    }
  }

  const handleGenerateApiKey = async () => {
    if (!apiKeyForm.name.trim()) {
      alert('Please enter a name for the API key')
      return
    }
    
    setApiKeyLoading(true)
    try {
      const response = await api.post('/users/me/api-keys', {
        name: apiKeyForm.name,
        description: apiKeyForm.description || undefined
      })
      setApiKeyForm({ name: '', description: '' })
      alert(`API Key generated successfully: ${response.data.key}`)
    } catch (error: any) {
      console.error('Failed to generate API key:', error)
      const message = error.response?.data?.detail || 'Failed to generate API key'
      alert(message)
    } finally {
      setApiKeyLoading(false)
    }
  }

  const loadMembers = async () => {
    if (organizations.length === 0) return
    
    setMembersLoading(true)
    try {
      // Use the first organization for now
      const orgId = organizations[0].id
      const response = await api.get(`/organizations/${orgId}/members`)
      setMembers(response.data)
    } catch (error) {
      console.error('Failed to load members:', error)
      setMembers([])
    } finally {
      setMembersLoading(false)
    }
  }

  const handleInviteMember = async () => {
    if (!inviteForm.email.trim()) {
      alert('Please enter an email address')
      return
    }
    
    if (organizations.length === 0) {
      alert('No organization found')
      return
    }
    
    setInviteLoading(true)
    try {
      const orgId = organizations[0].id
      await api.post(`/organizations/${orgId}/members/invite`, {
        email: inviteForm.email,
        role: inviteForm.role
      })
      setInviteForm({ email: '', role: 'member' })
      alert('Member invited successfully')
      await loadMembers()
    } catch (error: any) {
      console.error('Failed to invite member:', error)
      const message = error.response?.data?.detail || 'Failed to invite member'
      alert(message)
    } finally {
      setInviteLoading(false)
    }
  }

  const handleCreateUser = async () => {
    if (!createUserForm.first_name.trim()) {
      alert('Please enter first name')
      return
    }
    
    if (!createUserForm.last_name.trim()) {
      alert('Please enter last name')
      return
    }
    
    if (!createUserForm.email.trim()) {
      alert('Please enter email address')
      return
    }
    
    // Check if email already exists in current members
    const emailExists = members.some(member => 
      member.email.toLowerCase() === createUserForm.email.toLowerCase()
    )
    if (emailExists) {
      alert('A user with this email address already exists in the organization')
      return
    }
    
    if (!createUserForm.password.trim()) {
      alert('Please enter password')
      return
    }
    
    if (createUserForm.password.length < 8) {
      alert('Password must be at least 8 characters long')
      return
    }
    
    if (organizations.length === 0) {
      alert('No organization found')
      return
    }
    
    setCreateUserLoading(true)
    try {
      const orgId = organizations[0].id
      await api.post(`/organizations/${orgId}/members/create`, {
        first_name: createUserForm.first_name,
        last_name: createUserForm.last_name,
        email: createUserForm.email,
        password: createUserForm.password,
        role: createUserForm.role
      })
      setCreateUserForm({ first_name: '', last_name: '', email: '', password: '', role: 'member' })
      setShowCreateUserForm(false)
      alert('User created successfully')
      await loadMembers()
    } catch (error: any) {
      console.error('Failed to create user:', error)
      let message = 'Failed to create user'
      
      if (error.response?.data?.detail) {
        const detail = error.response.data.detail
        // If detail is an object with a message field
        if (typeof detail === 'object' && detail.message) {
          message = detail.message
        } else if (typeof detail === 'string') {
          message = detail
        }
      } else if (error.response?.data?.message) {
        message = error.response.data.message
      }
      
      alert(message)
    } finally {
      setCreateUserLoading(false)
    }
  }

  const handleUpdateMember = async (memberId: string, role: string) => {
    if (organizations.length === 0) return
    
    try {
      const orgId = organizations[0].id
      await api.patch(`/organizations/${orgId}/members/${memberId}`, { role })
      alert('Member role updated successfully')
      await loadMembers()
    } catch (error: any) {
      console.error('Failed to update member:', error)
      const message = error.response?.data?.detail || 'Failed to update member'
      alert(message)
    }
  }

  const handleRemoveMember = async (memberId: string, memberEmail: string) => {
    if (!confirm(`Are you sure you want to remove ${memberEmail} from the organization?`)) {
      return
    }
    
    if (organizations.length === 0) return
    
    try {
      const orgId = organizations[0].id
      await api.delete(`/organizations/${orgId}/members/${memberId}`)
      alert('Member removed successfully')
      await loadMembers()
    } catch (error: any) {
      console.error('Failed to remove member:', error)
      const message = error.response?.data?.detail || 'Failed to remove member'
      alert(message)
    }
  }


  const tabs = [
    { id: 'organization', label: 'Organization', icon: Building2 },
    { id: 'team', label: 'Team Members', icon: Users },
    { id: 'security', label: 'Security', icon: Shield }
  ]

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-6 space-y-6">
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
        <div className="bg-white rounded-lg border border-gray-200">
          {activeTab === 'organization' && (
            <div className="space-y-6 p-6">
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
            <div className="space-y-6 p-6">
              <h2 className="text-xl font-semibold text-gray-900">Team Members</h2>
              <p className="text-gray-600">Manage team members and permissions</p>
              
              {/* Create User Directly */}
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="p-4 border-b border-gray-200 flex items-center justify-between">
                  <h3 className="font-medium text-gray-900">Create New User</h3>
                  <button
                    onClick={() => setShowCreateUserForm(!showCreateUserForm)}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm flex items-center space-x-2"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Create User</span>
                  </button>
                </div>

                {showCreateUserForm && (
                  <div className="p-4 border-b border-gray-200 bg-gray-50">
                    <div className="space-y-4 max-w-4xl">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            First Name *
                          </label>
                          <input
                            type="text"
                            value={createUserForm.first_name}
                            onChange={(e) => setCreateUserForm({ ...createUserForm, first_name: e.target.value })}
                            placeholder="John"
                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Last Name *
                          </label>
                          <input
                            type="text"
                            value={createUserForm.last_name}
                            onChange={(e) => setCreateUserForm({ ...createUserForm, last_name: e.target.value })}
                            placeholder="Doe"
                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Email Address *
                          </label>
                          <input
                            type="email"
                            value={createUserForm.email}
                            onChange={(e) => setCreateUserForm({ ...createUserForm, email: e.target.value })}
                            placeholder="john.doe@example.com"
                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Password *
                          </label>
                          <input
                            type="password"
                            value={createUserForm.password}
                            onChange={(e) => setCreateUserForm({ ...createUserForm, password: e.target.value })}
                            placeholder="Minimum 8 characters"
                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                          />
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Role
                          </label>
                          <select
                            value={createUserForm.role}
                            onChange={(e) => setCreateUserForm({ ...createUserForm, role: e.target.value })}
                            className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                          >
                            <option value="member">Member</option>
                            <option value="admin">Admin</option>
                            <option value="viewer">Viewer</option>
                          </select>
                        </div>
                        <div className="flex items-end space-x-2">
                          <button
                            onClick={handleCreateUser}
                            disabled={createUserLoading || !createUserForm.first_name.trim() || !createUserForm.last_name.trim() || !createUserForm.email.trim() || !createUserForm.password.trim()}
                            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded text-sm"
                          >
                            {createUserLoading ? 'Creating...' : 'Create User'}
                          </button>
                          <button
                            onClick={() => {
                              setShowCreateUserForm(false)
                              setCreateUserForm({ first_name: '', last_name: '', email: '', password: '', role: 'member' })
                            }}
                            className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded text-sm"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
              
              {/* Invite New Member */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-4">Invite New Member</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      value={inviteForm.email}
                      onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                      placeholder="user@example.com"
                      className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Role
                    </label>
                    <select
                      value={inviteForm.role}
                      onChange={(e) => setInviteForm({ ...inviteForm, role: e.target.value })}
                      className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                    >
                      <option value="member">Member</option>
                      <option value="admin">Admin</option>
                      <option value="viewer">Viewer</option>
                    </select>
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={handleInviteMember}
                      disabled={inviteLoading || !inviteForm.email.trim()}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded text-sm"
                    >
                      {inviteLoading ? 'Inviting...' : 'Invite Member'}
                    </button>
                  </div>
                </div>
              </div>

              {/* Current Members */}
              <div className="bg-white rounded-lg border border-gray-200">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="font-medium text-gray-900">Current Members</h3>
                </div>
                
                {membersLoading ? (
                  <div className="p-8 text-center">
                    <p className="text-gray-600">Loading members...</p>
                  </div>
                ) : members.length === 0 ? (
                  <div className="p-8 text-center">
                    <Users className="h-12 w-12 text-gray-500 mx-auto mb-3" />
                    <p className="text-gray-600">No team members found</p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {members.map((member) => (
                      <div key={member.id} className="p-4 flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3">
                            <div className="h-8 w-8 bg-gray-500 rounded-full flex items-center justify-center">
                              <span className="text-white text-sm font-medium">
                                {member.full_name ? member.full_name.charAt(0).toUpperCase() : member.email.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium text-gray-900">
                                {member.full_name || member.username}
                                {member.is_current_user && (
                                  <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded">You</span>
                                )}
                              </p>
                              <p className="text-gray-600 text-sm">{member.email}</p>
                              <p className="text-gray-500 text-xs">
                                Joined {new Date(member.joined_at).toLocaleDateString()}
                                {member.last_login && ` • Last login ${new Date(member.last_login).toLocaleDateString()}`}
                              </p>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-3">
                          <select
                            value={member.role}
                            onChange={(e) => handleUpdateMember(member.id, e.target.value)}
                            disabled={member.is_current_user}
                            className="bg-white border border-gray-300 rounded px-2 py-1 text-sm text-gray-900 disabled:bg-gray-100"
                          >
                            <option value="viewer">Viewer</option>
                            <option value="member">Member</option>
                            <option value="admin">Admin</option>
                          </select>
                          
                          {!member.is_current_user && (
                            <button
                              onClick={() => handleRemoveMember(member.id, member.email)}
                              className="text-red-600 hover:text-red-800 text-sm px-2 py-1"
                            >
                              Remove
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6 p-6">
              <h2 className="text-xl font-semibold text-gray-900">Security Settings</h2>
              
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-4">Change Password</h3>
                  <div className="space-y-3 max-w-md">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Current Password
                      </label>
                      <input
                        type="password"
                        value={passwordForm.currentPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        New Password
                      </label>
                      <input
                        type="password"
                        value={passwordForm.newPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        value={passwordForm.confirmPassword}
                        onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                      />
                    </div>
                    <button
                      onClick={handleChangePassword}
                      disabled={passwordLoading || !passwordForm.currentPassword || !passwordForm.newPassword || !passwordForm.confirmPassword}
                      className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded text-sm"
                    >
                      {passwordLoading ? 'Changing...' : 'Change Password'}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}


        </div>
      </div>
    </ProtectedRoute>
  )
}