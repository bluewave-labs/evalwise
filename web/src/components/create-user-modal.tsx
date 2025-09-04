'use client'

import { useState } from 'react'
import { X, User, Eye, EyeOff } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface NewUser {
  email: string
  username: string
  password: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  rate_limit_tier: string
}

interface CreateUserModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (user: NewUser) => Promise<void>
  isLoading?: boolean
  error?: string | null
}

export default function CreateUserModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  isLoading = false,
  error = null
}: CreateUserModalProps) {
  const [newUser, setNewUser] = useState<NewUser>({
    email: '',
    username: '',
    password: '',
    full_name: '',
    is_active: true,
    is_superuser: false,
    rate_limit_tier: 'basic'
  })
  const [showPassword, setShowPassword] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newUser.email || !newUser.username || !newUser.password) return
    
    try {
      await onSubmit(newUser)
      // Reset form on success
      setNewUser({
        email: '',
        username: '',
        password: '',
        full_name: '',
        is_active: true,
        is_superuser: false,
        rate_limit_tier: 'basic'
      })
      onClose()
    } catch (error) {
      // Error handling is done by parent component
    }
  }

  const handleClose = () => {
    setNewUser({
      email: '',
      username: '',
      password: '',
      full_name: '',
      is_active: true,
      is_superuser: false,
      rate_limit_tier: 'basic'
    })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <User className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-bold text-gray-900">Create New User</h2>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="modal-email">Email *</Label>
            <Input
              id="modal-email"
              type="email"
              value={newUser.email}
              onChange={(e) => setNewUser({...newUser, email: e.target.value})}
              className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
              required
              disabled={isLoading}
            />
          </div>

          <div>
            <Label htmlFor="modal-username">Username *</Label>
            <Input
              id="modal-username"
              value={newUser.username}
              onChange={(e) => setNewUser({...newUser, username: e.target.value})}
              className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
              required
              disabled={isLoading}
            />
          </div>

          <div>
            <Label htmlFor="modal-password">Password *</Label>
            <div className="relative">
              <Input
                id="modal-password"
                type={showPassword ? "text" : "password"}
                value={newUser.password}
                onChange={(e) => setNewUser({...newUser, password: e.target.value})}
                className="w-full bg-white border border-gray-300 rounded px-3 py-2 pr-10 text-gray-900"
                required
                disabled={isLoading}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                disabled={isLoading}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <div>
            <Label htmlFor="modal-fullname">Full Name</Label>
            <Input
              id="modal-fullname"
              value={newUser.full_name}
              onChange={(e) => setNewUser({...newUser, full_name: e.target.value})}
              className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
              disabled={isLoading}
            />
          </div>

          <div className="flex space-x-6">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={newUser.is_active}
                onChange={(e) => setNewUser({...newUser, is_active: e.target.checked})}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                disabled={isLoading}
              />
              <span className="text-sm text-gray-700">Active</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={newUser.is_superuser}
                onChange={(e) => setNewUser({...newUser, is_superuser: e.target.checked})}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                disabled={isLoading}
              />
              <span className="text-sm text-gray-700">Admin</span>
            </label>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-4">
            <Button 
              type="button" 
              variant="secondary" 
              onClick={handleClose}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="submit"
              disabled={!newUser.email || !newUser.username || !newUser.password || isLoading}
            >
              {isLoading ? 'Creating...' : 'Create User'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}