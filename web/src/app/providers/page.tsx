'use client'

import { useState, useEffect } from 'react'
import { Key, Plus, Edit, Trash2, Eye, EyeOff } from 'lucide-react'

interface Provider {
  id: string
  name: string
  provider_type: 'openai' | 'ollama' | 'azure_openai'
  api_key?: string
  base_url?: string
  model_defaults: {
    model_name: string
    temperature: number
    max_tokens: number
  }
  is_default: boolean
  created_at: string
}

export default function ProvidersPage() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null)
  const [showApiKeys, setShowApiKeys] = useState<{[key: string]: boolean}>({})
  
  const [formData, setFormData] = useState({
    name: '',
    provider_type: 'openai' as 'openai' | 'ollama' | 'azure_openai',
    api_key: '',
    base_url: '',
    model_defaults: {
      model_name: 'gpt-3.5-turbo',
      temperature: 0.7,
      max_tokens: 1000
    },
    is_default: false
  })

  useEffect(() => {
    loadProviders()
  }, [])

  const loadProviders = async () => {
    try {
      // For now, we'll simulate with localStorage
      const savedProviders = localStorage.getItem('evalwise_providers')
      if (savedProviders) {
        setProviders(JSON.parse(savedProviders))
      }
    } catch (error) {
      console.error('Failed to load providers:', error)
    } finally {
      setLoading(false)
    }
  }

  const saveProvider = async (e: React.FormEvent) => {
    e.preventDefault()
    
    try {
      const newProvider: Provider = {
        id: editingProvider?.id || Date.now().toString(),
        ...formData,
        created_at: editingProvider?.created_at || new Date().toISOString()
      }

      let updatedProviders
      if (editingProvider) {
        updatedProviders = providers.map(p => p.id === editingProvider.id ? newProvider : p)
      } else {
        updatedProviders = [...providers, newProvider]
      }

      // If this is set as default, unset others
      if (newProvider.is_default) {
        updatedProviders = updatedProviders.map(p => ({
          ...p,
          is_default: p.id === newProvider.id
        }))
      }

      setProviders(updatedProviders)
      localStorage.setItem('evalwise_providers', JSON.stringify(updatedProviders))
      
      // Reset form
      setShowCreateForm(false)
      setEditingProvider(null)
      setFormData({
        name: '',
        provider_type: 'openai',
        api_key: '',
        base_url: '',
        model_defaults: {
          model_name: 'gpt-3.5-turbo',
          temperature: 0.7,
          max_tokens: 1000
        },
        is_default: false
      })
    } catch (error) {
      console.error('Failed to save provider:', error)
      alert('Failed to save provider')
    }
  }

  const deleteProvider = async (providerId: string) => {
    if (!confirm('Are you sure you want to delete this provider?')) return
    
    try {
      const updatedProviders = providers.filter(p => p.id !== providerId)
      setProviders(updatedProviders)
      localStorage.setItem('evalwise_providers', JSON.stringify(updatedProviders))
    } catch (error) {
      console.error('Failed to delete provider:', error)
      alert('Failed to delete provider')
    }
  }

  const editProvider = (provider: Provider) => {
    setEditingProvider(provider)
    setFormData({
      name: provider.name,
      provider_type: provider.provider_type,
      api_key: provider.api_key || '',
      base_url: provider.base_url || '',
      model_defaults: provider.model_defaults,
      is_default: provider.is_default
    })
    setShowCreateForm(true)
  }

  const toggleApiKeyVisibility = (providerId: string) => {
    setShowApiKeys(prev => ({
      ...prev,
      [providerId]: !prev[providerId]
    }))
  }

  const getProviderIcon = (type: string) => {
    switch (type) {
      case 'openai':
        return '🤖'
      case 'ollama':
        return '🦙'
      case 'azure_openai':
        return '☁️'
      default:
        return '⚙️'
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
          <h1 className="text-3xl font-bold text-gray-900">LLM Providers</h1>
          <p className="text-gray-600 mt-1">Manage your LLM API keys and configurations</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>Add Provider</span>
        </button>
      </div>

      {/* Create/Edit Provider Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            {editingProvider ? 'Edit Provider' : 'Add New Provider'}
          </h2>
          <form onSubmit={saveProvider} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Provider Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                  placeholder="My OpenAI Account"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Provider Type
                </label>
                <select
                  value={formData.provider_type}
                  onChange={(e) => setFormData({
                    ...formData, 
                    provider_type: e.target.value as any,
                    model_defaults: {
                      ...formData.model_defaults,
                      model_name: e.target.value === 'openai' ? 'gpt-3.5-turbo' : 
                                   e.target.value === 'ollama' ? 'llama2:7b' : 'gpt-35-turbo'
                    }
                  })}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                >
                  <option value="openai">OpenAI</option>
                  <option value="ollama">Ollama (Local)</option>
                  <option value="azure_openai">Azure OpenAI</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {formData.provider_type !== 'ollama' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    API Key
                  </label>
                  <input
                    type="password"
                    value={formData.api_key}
                    onChange={(e) => setFormData({...formData, api_key: e.target.value})}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                    placeholder="sk-..."
                    required
                  />
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Base URL {formData.provider_type === 'ollama' ? '(Required)' : '(Optional)'}
                </label>
                <input
                  type="url"
                  value={formData.base_url}
                  onChange={(e) => setFormData({...formData, base_url: e.target.value})}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                  placeholder={
                    formData.provider_type === 'ollama' ? 'http://localhost:11434' :
                    formData.provider_type === 'azure_openai' ? 'https://your-resource.openai.azure.com' :
                    'https://api.openai.com/v1'
                  }
                  required={formData.provider_type === 'ollama'}
                />
              </div>
            </div>

            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-3">Default Model Settings</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Default Model
                  </label>
                  <input
                    type="text"
                    value={formData.model_defaults.model_name}
                    onChange={(e) => setFormData({
                      ...formData,
                      model_defaults: {...formData.model_defaults, model_name: e.target.value}
                    })}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                    placeholder="gpt-3.5-turbo, llama2:7b, gpt-35-turbo"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Temperature
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={formData.model_defaults.temperature}
                    onChange={(e) => setFormData({
                      ...formData,
                      model_defaults: {...formData.model_defaults, temperature: parseFloat(e.target.value)}
                    })}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="8000"
                    value={formData.model_defaults.max_tokens}
                    onChange={(e) => setFormData({
                      ...formData,
                      model_defaults: {...formData.model_defaults, max_tokens: parseInt(e.target.value)}
                    })}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="flex items-center text-gray-700">
                <input
                  type="checkbox"
                  checked={formData.is_default}
                  onChange={(e) => setFormData({...formData, is_default: e.target.checked})}
                  className="mr-2"
                />
                Set as default provider
              </label>
            </div>

            <div className="flex space-x-3">
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                {editingProvider ? 'Update Provider' : 'Add Provider'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false)
                  setEditingProvider(null)
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Providers List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {providers.map((provider) => (
          <div key={provider.id} className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{getProviderIcon(provider.provider_type)}</span>
                <div>
                  <h3 className="font-semibold text-gray-900">{provider.name}</h3>
                  <p className="text-gray-600 text-sm capitalize">
                    {provider.provider_type.replace('_', ' ')}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                {provider.is_default && (
                  <span className="px-2 py-1 bg-blue-600 text-blue-100 text-xs rounded">
                    Default
                  </span>
                )}
                <button
                  onClick={() => editProvider(provider)}
                  className="p-1 text-gray-600 hover:text-gray-900"
                >
                  <Edit className="h-4 w-4" />
                </button>
                <button
                  onClick={() => deleteProvider(provider.id)}
                  className="p-1 text-gray-600 hover:text-red-600"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="space-y-2 text-sm text-gray-700">
              {provider.api_key && (
                <div className="flex items-center justify-between">
                  <span>API Key:</span>
                  <div className="flex items-center space-x-2">
                    <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                      {showApiKeys[provider.id] ? provider.api_key : '••••••••••••••••'}
                    </code>
                    <button
                      onClick={() => toggleApiKeyVisibility(provider.id)}
                      className="text-gray-600 hover:text-gray-900"
                    >
                      {showApiKeys[provider.id] ? 
                        <EyeOff className="h-4 w-4" /> : 
                        <Eye className="h-4 w-4" />
                      }
                    </button>
                  </div>
                </div>
              )}
              
              {provider.base_url && (
                <div className="flex items-center justify-between">
                  <span>Base URL:</span>
                  <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                    {provider.base_url}
                  </code>
                </div>
              )}
              
              <div className="flex items-center justify-between">
                <span>Default Model:</span>
                <code className="bg-gray-700 px-2 py-1 rounded text-xs">
                  {provider.model_defaults.model_name}
                </code>
              </div>
              
              <div className="flex items-center justify-between">
                <span>Temperature:</span>
                <span>{provider.model_defaults.temperature}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <span>Max Tokens:</span>
                <span>{provider.model_defaults.max_tokens}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {providers.length === 0 && (
        <div className="text-center py-12">
          <Key className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No providers configured</h3>
          <p className="text-gray-600 mb-4">Add your first LLM provider to get started</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Add Provider
          </button>
        </div>
      )}
    </div>
  )
}