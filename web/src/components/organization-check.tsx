'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/contexts/auth-context'
import OrganizationSetupModal from './organization-setup-modal'
import { api } from '@/lib/api'

export default function OrganizationCheck({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const [showOrgSetup, setShowOrgSetup] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  useEffect(() => {
    // Check if user exists and has no organizations
    if (user && (!user.organizations || user.organizations.length === 0)) {
      setShowOrgSetup(true)
    } else {
      setShowOrgSetup(false)
    }
  }, [user])

  const handleCreateOrganization = async (orgData: { name: string; description?: string }) => {
    setIsCreating(true)
    try {
      // Create organization via API
      const response = await api.post('/organizations', orgData)
      
      // Refresh user data to get updated organization list
      // This would typically be handled by refreshing the auth context
      window.location.reload() // Simple reload for now
      
    } catch (error) {
      console.error('Failed to create organization:', error)
      alert('Failed to create organization. Please try again.')
      setIsCreating(false)
    }
  }

  return (
    <>
      <OrganizationSetupModal 
        isOpen={showOrgSetup && !isCreating}
        onComplete={handleCreateOrganization}
      />
      {children}
    </>
  )
}