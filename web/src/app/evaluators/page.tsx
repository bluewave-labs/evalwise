'use client'

import { useState, useEffect } from 'react'
import { Key, Plus, Trash2, Eye, EyeOff } from 'lucide-react'
import { useAuth } from '@/contexts/auth-context'
import { api } from '@/lib/api'
import ProtectedRoute from '@/components/protected-route'

export default function EvaluatorsPage() {
  const { user } = useAuth()
  const [organizations, setOrganizations] = useState<any[]>([])
  const [llmKeys, setLlmKeys] = useState<any[]>([])
  const [llmKeysLoading, setLlmKeysLoading] = useState(true)
  const [initialLoad, setInitialLoad] = useState(true)
  const [showAddLlmKeyForm, setShowAddLlmKeyForm] = useState(false)
  const [llmKeyForm, setLlmKeyForm] = useState({
    provider: 'openai',
    key_name: '',
    api_key: '',
    endpoint_url: '',
    model_deployment_name: '',
    api_version: ''
  })
  const [llmKeyLoading, setLlmKeyLoading] = useState(false)
  const [showApiKey, setShowApiKey] = useState(false)

  useEffect(() => {
    const loadData = async () => {
      try {
        await loadOrganizations()
      } finally {
        setInitialLoad(false)
      }
    }
    loadData()
  }, [user])

  useEffect(() => {
    if (organizations.length > 0) {
      loadLlmKeys()
    } else if (!initialLoad) {
      setLlmKeysLoading(false)
    }
  }, [organizations, initialLoad])

  const loadOrganizations = async () => {
    if (!user) {
      setLlmKeysLoading(false)
      return
    }
    
    try {
      // Use user's organizations for now
      if (user.organizations && user.organizations.length > 0) {
        const userOrgs = user.organizations.map(org => ({
          id: org.id,
          name: org.name,
          role: org.role,
          created_at: new Date().toISOString(),
          member_count: 1
        }))
        setOrganizations(userOrgs)
      } else {
        console.log('No organizations found for user')
        setOrganizations([])
        setLlmKeysLoading(false)
      }
    } catch (error) {
      console.error('Failed to load organizations:', error)
      setOrganizations([])
      setLlmKeysLoading(false)
    }
  }

  const loadLlmKeys = async () => {
    if (organizations.length === 0) {
      setLlmKeysLoading(false)
      setLlmKeys([])
      return
    }
    
    setLlmKeysLoading(true)
    try {
      const orgId = organizations[0].id
      const response = await api.get(`/organizations/${orgId}/llm-keys`)
      setLlmKeys(response.data)
    } catch (error) {
      console.error('Failed to load evaluator keys:', error)
      setLlmKeys([])
    } finally {
      setLlmKeysLoading(false)
    }
  }

  const handleAddLlmKey = async () => {
    const requiredFields = getProviderRequiredFields(llmKeyForm.provider)
    
    if (!llmKeyForm.key_name.trim()) {
      alert('Please enter a key name')
      return
    }
    
    // For cloud providers, API key is required
    if (requiredFields.includes('api_key') && ['openai', 'azure_openai'].includes(llmKeyForm.provider) && !llmKeyForm.api_key.trim()) {
      alert('Please enter an API key')
      return
    }
    
    if (requiredFields.includes('endpoint_url') && !llmKeyForm.endpoint_url.trim()) {
      alert('Please enter an endpoint URL')
      return
    }
    
    if (organizations.length === 0) {
      alert('No organization found')
      return
    }
    
    setLlmKeyLoading(true)
    try {
      const orgId = organizations[0].id
      
      console.log('Submitting evaluator key:', {
        provider: llmKeyForm.provider,
        key_name: llmKeyForm.key_name,
        api_key: llmKeyForm.api_key ? '[REDACTED]' : 'EMPTY',
        endpoint_url: llmKeyForm.endpoint_url || undefined,
        model_deployment_name: llmKeyForm.model_deployment_name || undefined,
        api_version: llmKeyForm.api_version || undefined
      })
      
      await api.post(`/organizations/${orgId}/llm-keys`, {
        provider: llmKeyForm.provider,
        key_name: llmKeyForm.key_name,
        api_key: llmKeyForm.api_key,
        endpoint_url: llmKeyForm.endpoint_url || undefined,
        model_deployment_name: llmKeyForm.model_deployment_name || undefined,
        api_version: llmKeyForm.api_version || undefined
      })
      
      // Reset form
      setLlmKeyForm({
        provider: 'openai',
        key_name: '',
        api_key: '',
        endpoint_url: '',
        model_deployment_name: '',
        api_version: ''
      })
      setShowAddLlmKeyForm(false)
      alert('Evaluator key added successfully')
      await loadLlmKeys()
    } catch (error: any) {
      console.error('Failed to add evaluator key:', error)
      let message = 'Failed to add evaluator key'
      
      if (error.response?.data?.detail) {
        if (typeof error.response.data.detail === 'string') {
          message = error.response.data.detail
        } else if (error.response.data.detail?.message) {
          message = error.response.data.detail.message
        }
      } else if (error.message) {
        message = error.message
      }
      
      alert(message)
    } finally {
      setLlmKeyLoading(false)
    }
  }

  const handleDeleteLlmKey = async (keyId: string, keyName: string) => {
    if (!confirm(`Are you sure you want to delete the "${keyName}" evaluator key?`)) {
      return
    }
    
    if (organizations.length === 0) return
    
    try {
      const orgId = organizations[0].id
      await api.delete(`/organizations/${orgId}/llm-keys/${keyId}`)
      alert('Evaluator key deleted successfully')
      await loadLlmKeys()
    } catch (error: any) {
      console.error('Failed to delete evaluator key:', error)
      const message = error.response?.data?.detail || 'Failed to delete evaluator key'
      alert(message)
    }
  }

  const getProviderDisplayName = (provider: string) => {
    const names: { [key: string]: string } = {
      'openai': 'OpenAI',
      'azure_openai': 'Azure OpenAI',
      'local_openai': 'Local OpenAI',
      'ollama': 'Ollama'
    }
    return names[provider] || provider
  }

  const getProviderRequiredFields = (provider: string) => {
    switch (provider) {
      case 'openai':
        return ['api_key']
      case 'azure_openai':
        return ['api_key', 'endpoint_url']
      case 'local_openai':
        return ['api_key', 'endpoint_url']
      case 'ollama':
        return ['endpoint_url']
      default:
        return ['api_key']
    }
  }

  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-6 space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Evaluators</h1>
          <p className="text-gray-600 mt-1">Manage your evaluation models and API keys</p>
        </div>
        
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-yellow-800 text-sm">
            <strong>Security:</strong> API keys are encrypted and stored securely. They are never displayed after creation.
          </p>
        </div>
        
        {/* Add New Evaluator Key */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h3 className="font-medium text-gray-900">API Keys</h3>
            <button
              onClick={() => setShowAddLlmKeyForm(!showAddLlmKeyForm)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm flex items-center space-x-2"
            >
              <Plus className="h-4 w-4" />
              <span>Add API Key</span>
            </button>
          </div>

          {showAddLlmKeyForm && (
            <div className="p-4 border-b border-gray-200 bg-gray-50">
              <div className="space-y-4 max-w-2xl">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Provider *
                    </label>
                    <select
                      value={llmKeyForm.provider}
                      onChange={(e) => setLlmKeyForm({ ...llmKeyForm, provider: e.target.value })}
                      className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                    >
                      <option value="openai">OpenAI</option>
                      <option value="azure_openai">Azure OpenAI</option>
                      <option value="local_openai">Local OpenAI</option>
                      <option value="ollama">Ollama</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Key Name *
                    </label>
                    <input
                      type="text"
                      value={llmKeyForm.key_name}
                      onChange={(e) => setLlmKeyForm({ ...llmKeyForm, key_name: e.target.value })}
                      placeholder="e.g., Production OpenAI Evaluator"
                      className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                    />
                  </div>
                </div>

                {getProviderRequiredFields(llmKeyForm.provider).includes('api_key') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Key {['local_openai', 'ollama'].includes(llmKeyForm.provider) ? '(Optional)' : '*'}
                      {llmKeyForm.provider === 'openai' && (
                        <span className="text-gray-500 text-xs ml-1">(starts with sk-)</span>
                      )}
                      {['local_openai', 'ollama'].includes(llmKeyForm.provider) && (
                        <span className="text-gray-500 text-xs ml-1">(leave empty for dummy key)</span>
                      )}
                    </label>
                    <div className="relative">
                      <input
                        type={showApiKey ? "text" : "password"}
                        value={llmKeyForm.api_key}
                        onChange={(e) => setLlmKeyForm({ ...llmKeyForm, api_key: e.target.value })}
                        placeholder={llmKeyForm.provider === 'openai' ? 'sk-...' : 'Enter API key'}
                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 pr-10 text-gray-900"
                      />
                      <button
                        type="button"
                        onClick={() => setShowApiKey(!showApiKey)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                )}

                {getProviderRequiredFields(llmKeyForm.provider).includes('endpoint_url') && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Endpoint URL *
                    </label>
                    <input
                      type="text"
                      value={llmKeyForm.endpoint_url}
                      onChange={(e) => setLlmKeyForm({ ...llmKeyForm, endpoint_url: e.target.value })}
                      placeholder={
                        llmKeyForm.provider === 'azure_openai' 
                          ? 'https://your-instance.openai.azure.com/'
                          : llmKeyForm.provider === 'ollama'
                          ? 'http://localhost:11434'
                          : 'http://localhost:1234/v1'
                      }
                      className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                    />
                  </div>
                )}

                {llmKeyForm.provider === 'azure_openai' && (
                  <>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Model Deployment Name (optional)
                      </label>
                      <input
                        type="text"
                        value={llmKeyForm.model_deployment_name}
                        onChange={(e) => setLlmKeyForm({ ...llmKeyForm, model_deployment_name: e.target.value })}
                        placeholder="gpt-4"
                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        API Version (optional)
                      </label>
                      <input
                        type="text"
                        value={llmKeyForm.api_version}
                        onChange={(e) => setLlmKeyForm({ ...llmKeyForm, api_version: e.target.value })}
                        placeholder="2023-12-01-preview"
                        className="w-full bg-white border border-gray-300 rounded px-3 py-2 text-gray-900"
                      />
                    </div>
                  </>
                )}

                <div className="flex space-x-3">
                  <button
                    onClick={handleAddLlmKey}
                    disabled={llmKeyLoading || !llmKeyForm.key_name.trim()}
                    className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-4 py-2 rounded text-sm"
                  >
                    {llmKeyLoading ? 'Adding...' : 'Add API Key'}
                  </button>
                  <button
                    onClick={() => setShowAddLlmKeyForm(false)}
                    className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded text-sm"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Existing Evaluator Keys */}
          <div>
            {llmKeysLoading ? (
              <div className="p-8 text-center">
                <p className="text-gray-600">Loading API keys...</p>
              </div>
            ) : llmKeys.length === 0 ? (
              <div className="p-8 text-center">
                <Key className="h-12 w-12 text-gray-500 mx-auto mb-3" />
                <p className="text-gray-600">No API keys configured</p>
                <p className="text-gray-500 text-sm mt-1">Add API keys for providers like OpenAI to enable LLM evaluations</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {llmKeys.map((key) => (
                  <div key={key.id} className="p-4 flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Key className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{key.key_name}</p>
                          <p className="text-sm text-gray-600">
                            Provider: {getProviderDisplayName(key.provider)}
                          </p>
                          <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                            <span>Added {new Date(key.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <button
                      onClick={() => handleDeleteLlmKey(key.id, key.key_name)}
                      className="text-red-600 hover:text-red-800 p-2"
                      title="Delete API key"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </ProtectedRoute>
  )
}