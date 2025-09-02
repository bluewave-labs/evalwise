'use client'

import { useState } from 'react'
import { X, Building2 } from 'lucide-react'

interface OrganizationSetupModalProps {
  isOpen: boolean
  onComplete: (orgData: { name: string; description?: string }) => void
}

export default function OrganizationSetupModal({ 
  isOpen, 
  onComplete 
}: OrganizationSetupModalProps) {
  const [orgName, setOrgName] = useState('')
  const [orgDescription, setOrgDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  if (!isOpen) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!orgName.trim()) return

    setIsSubmitting(true)
    try {
      await onComplete({
        name: orgName.trim(),
        description: orgDescription.trim() || undefined
      })
    } catch (error) {
      console.error('Failed to create organization:', error)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6 shadow-xl">
        <div className="flex items-center space-x-3 mb-6">
          <Building2 className="h-8 w-8 text-blue-500" />
          <div>
            <h2 className="text-xl font-bold text-gray-900">Welcome to EvalWise!</h2>
            <p className="text-gray-600 text-sm">Let's set up your organization</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Organization Name *
            </label>
            <input
              type="text"
              value={orgName}
              onChange={(e) => setOrgName(e.target.value)}
              placeholder="e.g., Acme Corp, Personal Projects"
              className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-900"
              required
              autoFocus
              disabled={isSubmitting}
            />
            <p className="text-xs text-gray-500 mt-1">
              This will be your primary workspace for LLM evaluations
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (optional)
            </label>
            <textarea
              value={orgDescription}
              onChange={(e) => setOrgDescription(e.target.value)}
              placeholder="Brief description of your organization or project"
              className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-900 resize-none"
              rows={3}
              disabled={isSubmitting}
            />
          </div>

          <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-3">
            <p className="text-blue-300 text-sm">
              <strong>Note:</strong> You can manage organization settings and invite team members later from the Settings page.
            </p>
          </div>

          <button
            type="submit"
            disabled={!orgName.trim() || isSubmitting}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium rounded-lg px-4 transition-colors"
            style={{ height: '34px' }}
          >
            {isSubmitting ? 'Creating Organization...' : 'Create Organization'}
          </button>
        </form>
      </div>
    </div>
  )
}