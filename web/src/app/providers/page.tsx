'use client'

import { useState, useEffect } from 'react'
import { Key, X } from 'lucide-react'
import { useAuth } from '@/contexts/auth-context'
import { api } from '@/lib/api'

interface LLMProvider {
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

export default function ProvidersPage() {
  const { user } = useAuth()
  const [providers, setProviders] = useState<LLMProvider[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    provider_type: 'openai',
    api_key: '',
    base_url: '',
    model_name: '',
    is_default: false
  })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const orgId = user?.organizations?.[0]?.id

  useEffect(() => {
    if (orgId) {
      loadProviders()
    }
  }, [orgId])

  const loadProviders = async () => {
    if (!orgId) return

    try {
      setLoading(true)
      const response = await api.get(`/organizations/${orgId}/llm-providers`)
      setProviders(response.data)
    } catch (err: any) {
      console.error('Failed to load providers:', err)
      setError(err.response?.data?.message || 'Failed to load providers')
    } finally {
      setLoading(false)
    }
  }

  const openCreateModal = () => {
    setEditingProvider(null)
    setFormData({
      name: '',
      provider_type: 'openai',
      api_key: '',
      base_url: '',
      model_name: '',
      is_default: false
    })
    setError(null)
    setShowModal(true)
  }

  const openEditModal = (provider: LLMProvider) => {
    setEditingProvider(provider)
    setFormData({
      name: provider.name,
      provider_type: provider.provider_type,
      api_key: '',
      base_url: provider.base_url || '',
      model_name: provider.model_defaults?.model_name || '',
      is_default: provider.is_default
    })
    setError(null)
    setShowModal(true)
  }

  const closeModal = () => {
    setShowModal(false)
    setEditingProvider(null)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!orgId) {
      setError('No organization found')
      return
    }

    if (!formData.model_name.trim()) {
      setError('Model name is required')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
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

      if (formData.api_key) {
        payload.api_key = formData.api_key
      }

      if (formData.base_url) {
        payload.base_url = formData.base_url
      }

      if (editingProvider) {
        await api.put(`/organizations/${orgId}/llm-providers/${editingProvider.id}`, payload)
      } else {
        await api.post(`/organizations/${orgId}/llm-providers`, payload)
      }

      await loadProviders()
      closeModal()
    } catch (err: any) {
      console.error('Failed to save provider:', err)
      setError(err.response?.data?.message || err.response?.data?.detail || 'Failed to save provider')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (provider: LLMProvider) => {
    if (!orgId) return

    if (!confirm(`Delete "${provider.name}"? This cannot be undone.`)) {
      return
    }

    try {
      await api.delete(`/organizations/${orgId}/llm-providers/${provider.id}`)
      await loadProviders()
    } catch (err: any) {
      console.error('Failed to delete provider:', err)
      alert(err.response?.data?.message || 'Failed to delete provider')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">LLM Providers</h1>
            <p className="mt-1 text-gray-600">Manage your LLM API keys and configurations</p>
          </div>
          <button
            onClick={openCreateModal}
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
          >
            <span className="text-xl">+</span>
            <span>Add Provider</span>
          </button>
        </div>

        {/* Main Content */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
          {providers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24">
              <Key className="w-20 h-20 text-gray-400 mb-6" strokeWidth={1.5} />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">No providers configured</h2>
              <p className="text-gray-600 mb-6">Add your first LLM provider to get started</p>
              <button
                onClick={openCreateModal}
                className="bg-blue-600 text-white px-5 py-2.5 rounded-lg hover:bg-blue-700"
              >
                Add Provider
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Model</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {providers.map((provider) => (
                    <tr key={provider.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 text-sm font-medium text-gray-900">{provider.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">{provider.provider_type}</td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {provider.model_defaults?.model_name || '-'}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {provider.is_default && (
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                            Default
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(provider.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm text-right space-x-3">
                        <button
                          onClick={() => openEditModal(provider)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(provider)}
                          className="text-red-600 hover:text-red-800"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h3 className="text-xl font-semibold text-gray-900">
                {editingProvider ? 'Edit Provider' : 'Add Provider'}
              </h3>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6">
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                  {typeof error === 'string' ? error : JSON.stringify(error)}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="azure_openai">Azure OpenAI</option>
                    <option value="cohere">Cohere</option>
                    <option value="google">Google</option>
                    <option value="local_openai">Local OpenAI</option>
                    <option value="ollama">Ollama</option>
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder={editingProvider ? 'Leave blank to keep existing' : 'sk-...'}
                  />
                  {editingProvider && (
                    <p className="mt-1 text-xs text-gray-500">Leave blank to keep existing API key</p>
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="https://api.openai.com/v1"
                  />
                  <p className="mt-1 text-xs text-gray-500">Optional: Custom API endpoint URL</p>
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="gpt-4"
                  />
                  <p className="mt-1 text-xs text-gray-500">Default model for this provider</p>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_default"
                    checked={formData.is_default}
                    onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="is_default" className="ml-2 text-sm text-gray-700">
                    Set as default provider
                  </label>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={closeModal}
                  disabled={submitting}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : editingProvider ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
