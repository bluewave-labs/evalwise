'use client'

import { useState, useEffect } from 'react'
import { Plus, Key, X } from 'lucide-react'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/auth-context'

interface Provider {
  id: string
  name: string
  provider_type: string
  base_url?: string
  model_defaults?: {
    model_name?: string
    temperature?: number
    max_tokens?: number
  }
  is_default: boolean
  created_at: string
}

interface ProviderFormData {
  name: string
  provider_type: string
  api_key: string
  base_url?: string
  model_name?: string
  is_default: boolean
}

export default function ProvidersContent() {
  const { user } = useAuth()
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null)
  const [formData, setFormData] = useState<ProviderFormData>({
    name: '',
    provider_type: 'openai',
    api_key: '',
    base_url: '',
    model_name: '',
    is_default: false
  })
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const organizationId = user?.organizations?.[0]?.id

  useEffect(() => {
    if (organizationId) {
      fetchProviders()
    }
  }, [organizationId])

  const fetchProviders = async () => {
    if (!organizationId) {
      setError('No organization found')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const response = await api.get(`/organizations/${organizationId}/llm-providers`)
      setProviders(response.data)
    } catch (err: any) {
      console.error('Failed to fetch providers:', err)
      const errorMessage = err.response?.data?.message || err.response?.data?.detail || err.message || 'Failed to load providers'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const openCreateForm = () => {
    setEditingProvider(null)
    setFormData({
      name: '',
      provider_type: 'openai',
      api_key: '',
      base_url: '',
      model_name: '',
      is_default: false
    })
    setFormError(null)
    setShowForm(true)
  }

  const openEditForm = (provider: Provider) => {
    setEditingProvider(provider)
    setFormData({
      name: provider.name,
      provider_type: provider.provider_type,
      api_key: '',
      base_url: provider.base_url || '',
      model_name: provider.model_defaults?.model_name || '',
      is_default: provider.is_default
    })
    setFormError(null)
    setShowForm(true)
  }

  const closeForm = () => {
    setShowForm(false)
    setEditingProvider(null)
    setFormError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!organizationId) {
      setFormError('No organization found')
      return
    }

    setFormError(null)
    setSubmitting(true)

    try {
      // Validate model name
      if (!formData.model_name || !formData.model_name.trim()) {
        setFormError('Model name is required')
        setSubmitting(false)
        return
      }

      // Prepare payload matching API expectations
      const payload: any = {
        name: formData.name,
        provider_type: formData.provider_type,
        model_defaults: {
          model_name: formData.model_name.trim(),
          temperature: 0.7,
          max_tokens: 1000
        },
        is_default: formData.is_default
      }

      // Only include API key and base_url if provided
      if (formData.api_key) {
        payload.api_key = formData.api_key
      }
      if (formData.base_url) {
        payload.base_url = formData.base_url
      }

      if (editingProvider) {
        await api.put(`/organizations/${organizationId}/llm-providers/${editingProvider.id}`, payload)
      } else {
        await api.post(`/organizations/${organizationId}/llm-providers`, payload)
      }
      await fetchProviders()
      closeForm()
    } catch (err: any) {
      console.error('Failed to save provider:', err)
      const errorMessage = err.response?.data?.message || err.response?.data?.detail || err.message || 'Failed to save provider'
      setFormError(errorMessage)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (provider: Provider) => {
    if (!organizationId) {
      setError('No organization found')
      return
    }

    if (!confirm(`Are you sure you want to delete "${provider.name}"? This action cannot be undone.`)) {
      return
    }

    try {
      await api.delete(`/organizations/${organizationId}/llm-providers/${provider.id}`)
      await fetchProviders()
    } catch (err: any) {
      console.error('Failed to delete provider:', err)
      const errorMessage = err.response?.data?.message || err.response?.data?.detail || err.message || 'Failed to delete provider'
      setError(errorMessage)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">LLM Providers</h2>
          <p className="text-gray-600 mt-1">Manage your LLM API keys and configurations</p>
        </div>
        <button
          onClick={openCreateForm}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Add Provider</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </div>
      )}

      {providers.length === 0 ? (
        /* Empty State */
        <div className="text-center py-12">
          <Key className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No providers configured</h3>
          <p className="text-gray-600 mb-4">Add your first LLM provider to get started</p>
          <button
            onClick={openCreateForm}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Add Provider
          </button>
        </div>
      ) : (
        /* Providers List */
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {providers.map((provider) => (
                  <tr key={provider.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{provider.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{provider.provider_type}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{provider.model_defaults?.model_name || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {provider.is_default && (
                        <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                          Default
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(provider.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => openEditForm(provider)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(provider)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center p-6 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">
                {editingProvider ? 'Edit Provider' : 'Add Provider'}
              </h2>
              <button
                onClick={closeForm}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {formError && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                  {typeof formError === 'string' ? formError : JSON.stringify(formError)}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="My OpenAI Provider"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Provider Type *
                </label>
                <select
                  required
                  value={formData.provider_type}
                  onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="openai">OpenAI</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="azure">Azure OpenAI</option>
                  <option value="cohere">Cohere</option>
                  <option value="google">Google</option>
                  <option value="custom">Custom</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key *
                </label>
                <input
                  type="password"
                  required={!editingProvider}
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder={editingProvider ? 'Leave blank to keep existing' : 'sk-...'}
                />
                {editingProvider && (
                  <p className="text-xs text-gray-500 mt-1">Leave blank to keep the existing API key</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Base URL
                </label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.openai.com/v1"
                />
                <p className="text-xs text-gray-500 mt-1">Optional: Custom API endpoint URL</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Model Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.model_name}
                  onChange={(e) => setFormData({ ...formData, model_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="gpt-4"
                />
                <p className="text-xs text-gray-500 mt-1">Default model for this provider</p>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_default"
                  checked={formData.is_default}
                  onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_default" className="ml-2 block text-sm text-gray-700">
                  Set as default provider
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={closeForm}
                  disabled={submitting}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : editingProvider ? 'Update Provider' : 'Create Provider'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
