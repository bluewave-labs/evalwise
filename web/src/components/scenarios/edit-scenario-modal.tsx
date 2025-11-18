"use client"

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui'
import { api } from '@/lib/api'
import { X } from 'lucide-react'
import type { Scenario, ScenarioParams } from '@/types/scenarios'


interface EditScenarioModalProps {
  scenario: Scenario
  onClose: () => void
  onSuccess: (name: string) => void
}

export default function EditScenarioModal({ scenario, onClose, onSuccess }: EditScenarioModalProps) {
  const [name, setName] = useState(scenario.name)
  const [tags, setTags] = useState(scenario.tags.join(', '))
  const [params, setParams] = useState<ScenarioParams>(scenario.params_json)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!name.trim()) {
      setError('Name is required')
      return
    }

    try {
      setLoading(true)
      setError(null)
      
      const updateData = {
        name: name.trim(),
        params_json: params,
        tags: tags.split(',').map(t => t.trim()).filter(Boolean)
      }
      
      await api.put(`/scenarios/${scenario.id}`, updateData)
      onSuccess(name.trim())
    } catch (err: any) {
      console.error('Failed to update scenario:', err)
      setError(err.response?.data?.detail || 'Failed to update scenario')
    } finally {
      setLoading(false)
    }
  }

  const renderParamsEditor = () => {
    switch (scenario.type) {
      case 'jailbreak_basic':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Techniques
              </label>
              <div className="space-y-2">
                {['dan', 'roleplay', 'hypothetical', 'encoding', 'multilingual'].map(technique => (
                  <label key={technique} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={params.techniques?.includes(technique)}
                      onChange={(e) => {
                        const techniques = e.target.checked
                          ? [...(params.techniques || []), technique]
                          : (params.techniques || []).filter((t: string) => t !== technique)
                        setParams({ ...params, techniques } as ScenarioParams)
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 capitalize">{technique}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={params.randomize}
                  onChange={(e) => setParams({ ...params, randomize: e.target.checked })}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Randomize attack order</span>
              </label>
            </div>
          </div>
        )
      
      case 'safety_probe':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Safety Categories
              </label>
              <div className="space-y-2">
                {['violence', 'self_harm', 'hate_speech', 'illegal', 'sexual'].map(category => (
                  <label key={category} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={params.categories?.includes(category)}
                      onChange={(e) => {
                        const categories = e.target.checked
                          ? [...(params.categories || []), category]
                          : (params.categories || []).filter((c: string) => c !== category)
                        setParams({ ...params, categories } as ScenarioParams)
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 capitalize">{category.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Approach
              </label>
              <select
                value={params.directness || 'indirect'}
                onChange={(e) => setParams({ ...params, directness: e.target.value as 'direct' | 'indirect' | 'gradual' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="direct">Direct</option>
                <option value="indirect">Indirect</option>
                <option value="gradual">Gradual Escalation</option>
              </select>
            </div>
          </div>
        )
      
      case 'privacy_probe':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Probe Types
              </label>
              <div className="space-y-2">
                {['personal_info', 'system_prompt', 'training_data', 'api_keys'].map(probeType => (
                  <label key={probeType} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={params.probe_types?.includes(probeType)}
                      onChange={(e) => {
                        const probe_types = e.target.checked
                          ? [...(params.probe_types || []), probeType]
                          : (params.probe_types || []).filter((p: string) => p !== probeType)
                        setParams({ ...params, probe_types } as ScenarioParams)
                      }}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700 capitalize">{probeType.replace('_', ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Approach
              </label>
              <select
                value={params.approach || 'indirect'}
                onChange={(e) => setParams({ ...params, approach: e.target.value as 'direct' | 'indirect' | 'social_engineering' })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="direct">Direct</option>
                <option value="indirect">Indirect</option>
                <option value="social_engineering">Social Engineering</option>
              </select>
            </div>
          </div>
        )
      
      default:
        return (
          <div className="text-sm text-gray-500">
            Parameters for {scenario.type} are not editable through the UI.
          </div>
        )
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">Edit Scenario</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Scenario Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {/* Type (read-only) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Scenario Type
            </label>
            <input
              type="text"
              value={scenario.type}
              disabled
              className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              Type cannot be changed after creation
            </p>
          </div>

          {/* Parameters */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Parameters
            </label>
            <div className="border border-gray-200 rounded-md p-4 bg-gray-50">
              {renderParamsEditor()}
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g., safety, red-team, production"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Metadata */}
          <div className="bg-gray-50 rounded-md p-4">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Metadata</h3>
            <div className="space-y-1 text-sm text-gray-500">
              <div>Created: {new Date(scenario.created_at).toLocaleString()}</div>
              <div>Updated: {new Date(scenario.updated_at).toLocaleString()}</div>
              <div>ID: <code className="text-xs">{scenario.id}</code></div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-md">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}