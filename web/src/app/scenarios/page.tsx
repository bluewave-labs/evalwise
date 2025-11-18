"use client"

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/contexts/auth-context'
import { Button } from '@/components/ui'
import { api } from '@/lib/api'
import { 
  Plus, 
  Search, 
  FileText, 
  Shield, 
  Lock, 
  Brain,
  Edit,
  Trash2,
  Play,
  Copy,
  Filter,
  ChevronDown
} from 'lucide-react'
import CreateScenarioModal from '@/components/scenarios/create-scenario-modal'
import EditScenarioModal from '@/components/scenarios/edit-scenario-modal'
import ScenarioPreviewModal from '@/components/scenarios/scenario-preview-modal'
import { ScenarioListSkeleton } from '@/components/scenarios/loading-skeleton'
import { useToast, ToastProvider } from '@/components/scenarios/toast-notification'
import { useDebouncedValue } from '@/hooks/use-debounced-value'
import ProtectedRoute from '@/components/protected-route'
import type { Scenario, ScenarioTypeConfig } from '@/types/scenarios'

const scenarioTypeConfig: Record<string, ScenarioTypeConfig> = {
  jailbreak_basic: {
    label: 'Jailbreak',
    icon: Shield,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    description: 'Tests model resistance to prompt injection and jailbreak attempts'
  },
  safety_probe: {
    label: 'Safety',
    icon: Brain,
    color: 'text-orange-600', 
    bgColor: 'bg-orange-50',
    description: 'Probes safety boundaries and harmful content generation'
  },
  privacy_probe: {
    label: 'Privacy',
    icon: Lock,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    description: 'Tests for PII leakage and system information disclosure'
  }
}

function ScenariosPageContent() {
  const { isAuthenticated } = useAuth()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingScenario, setEditingScenario] = useState<Scenario | null>(null)
  const [previewingScenario, setPreviewingScenario] = useState<Scenario | null>(null)
  const debouncedSearchQuery = useDebouncedValue(searchQuery, 300)
  const { addToast } = useToast()

  useEffect(() => {
    let isCancelled = false
    
    if (isAuthenticated) {
      fetchScenarios().catch(() => {
        if (!isCancelled) {
          setError('Failed to load scenarios')
        }
      })
    }
    
    return () => {
      isCancelled = true
    }
  }, [isAuthenticated])

  const fetchScenarios = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await api.get('/scenarios')
      setScenarios(response.data)
    } catch (err: any) {
      console.error('Failed to fetch scenarios:', err)
      const errorMessage = err.response?.data?.detail || 'Failed to load scenarios'
      setError(errorMessage)
      addToast({
        type: 'error',
        title: 'Error loading scenarios',
        message: errorMessage
      })
    } finally {
      setLoading(false)
    }
  }, [addToast])

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"? This action cannot be undone.`)) return
    
    try {
      await api.delete(`/scenarios/${id}`)
      addToast({
        type: 'success',
        title: 'Scenario deleted',
        message: `"${name}" has been deleted successfully`
      })
      await fetchScenarios()
    } catch (err: any) {
      console.error('Failed to delete scenario:', err)
      const errorMessage = err.response?.data?.detail || 'Failed to delete scenario'
      addToast({
        type: 'error',
        title: 'Delete failed',
        message: errorMessage
      })
    }
  }

  const handleDuplicate = async (scenario: Scenario) => {
    try {
      const newScenario = {
        name: `${scenario.name} (Copy)`,
        type: scenario.type,
        params_json: scenario.params_json,
        tags: scenario.tags
      }
      await api.post('/scenarios', newScenario)
      addToast({
        type: 'success',
        title: 'Scenario duplicated',
        message: `Created copy of "${scenario.name}"`
      })
      await fetchScenarios()
    } catch (err: any) {
      console.error('Failed to duplicate scenario:', err)
      const errorMessage = err.response?.data?.detail || 'Failed to duplicate scenario'
      addToast({
        type: 'error',
        title: 'Duplicate failed',
        message: errorMessage
      })
    }
  }

  // Filter scenarios based on debounced search and selected types
  const filteredScenarios = scenarios.filter(scenario => {
    const matchesSearch = debouncedSearchQuery === '' || 
      scenario.name.toLowerCase().includes(debouncedSearchQuery.toLowerCase()) ||
      scenario.tags.some(tag => tag.toLowerCase().includes(debouncedSearchQuery.toLowerCase()))
    
    const matchesType = selectedTypes.length === 0 || selectedTypes.includes(scenario.type)
    
    return matchesSearch && matchesType
  })

  // Get unique scenario types for filter
  const availableTypes = Array.from(new Set(scenarios.map(s => s.type)))

  const toggleTypeFilter = (type: string) => {
    setSelectedTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    )
  }

  // This check is now redundant since ProtectedRoute handles it,
  // but keeping for extra safety in case ProtectedRoute is bypassed
  if (!isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Attack Scenarios</h1>
          <p className="text-gray-600">Manage adversarial testing patterns and red team strategies</p>
        </div>

        {/* Actions Bar */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <Button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Scenario
            </Button>

            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search scenarios..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Type Filters */}
            {availableTypes.length > 0 && (
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-gray-500" />
                {availableTypes.map(type => {
                  const config = scenarioTypeConfig[type as keyof typeof scenarioTypeConfig]
                  if (!config) return null
                  
                  return (
                    <button
                      key={type}
                      onClick={() => toggleTypeFilter(type)}
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        selectedTypes.includes(type)
                          ? `${config.bgColor} ${config.color}`
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {config.label}
                    </button>
                  )
                })}
                {selectedTypes.length > 0 && (
                  <button
                    onClick={() => setSelectedTypes([])}
                    className="text-sm text-gray-500 hover:text-gray-700"
                  >
                    Clear
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Scenarios Grid */}
        {loading ? (
          <ScenarioListSkeleton />
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">{error}</p>
            <Button onClick={fetchScenarios} className="mt-4">
              Retry
            </Button>
          </div>
        ) : filteredScenarios.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {debouncedSearchQuery || selectedTypes.length > 0 ? 'No scenarios found' : 'No scenarios yet'}
            </h3>
            <p className="text-gray-500 mb-4">
              {debouncedSearchQuery || selectedTypes.length > 0 
                ? 'Try adjusting your filters'
                : 'Create your first attack scenario to get started'}
            </p>
            {!debouncedSearchQuery && selectedTypes.length === 0 && (
              <Button onClick={() => setShowCreateModal(true)} className="bg-blue-600 hover:bg-blue-700 text-white">
                <Plus className="h-4 w-4 mr-2" />
                Create Scenario
              </Button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredScenarios.map(scenario => {
              const config = scenarioTypeConfig[scenario.type as keyof typeof scenarioTypeConfig] || {
                label: scenario.type,
                icon: FileText,
                color: 'text-gray-600',
                bgColor: 'bg-gray-50',
                description: ''
              }
              const Icon = config.icon

              return (
                <div
                  key={scenario.id}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-2 rounded-lg ${config.bgColor}`}>
                      <Icon className={`h-5 w-5 ${config.color}`} />
                    </div>
                    <span className={`text-xs font-medium px-2 py-1 rounded-full ${config.bgColor} ${config.color}`}>
                      {config.label}
                    </span>
                  </div>

                  {/* Content */}
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{scenario.name}</h3>
                  <p className="text-sm text-gray-500 mb-4 overflow-hidden" style={{display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical'}}>
                    {config.description}
                  </p>

                  {/* Tags */}
                  {scenario.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {scenario.tags.slice(0, 3).map(tag => (
                        <span
                          key={tag}
                          className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded-full"
                        >
                          {tag}
                        </span>
                      ))}
                      {scenario.tags.length > 3 && (
                        <span className="text-xs px-2 py-1 text-gray-500">
                          +{scenario.tags.length - 3} more
                        </span>
                      )}
                    </div>
                  )}

                  {/* Stats */}
                  <div className="text-sm text-gray-500 mb-4">
                    <div className="flex items-center justify-between">
                      <span>Variations:</span>
                      <span className="font-medium text-gray-700">
                        ~{scenario.type === 'jailbreak_basic' ? '15-20' : '10-15'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <span>Created:</span>
                      <span className="font-medium text-gray-700">
                        {new Date(scenario.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 pt-4 border-t border-gray-100">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setPreviewingScenario(scenario)}
                      className="flex-1"
                    >
                      <Play className="h-3 w-3 mr-1" />
                      Preview
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingScenario(scenario)}
                      className="flex-1"
                    >
                      <Edit className="h-3 w-3 mr-1" />
                      Edit
                    </Button>
                    <div className="relative">
                      <select
                        className="appearance-none bg-white border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        onChange={(e) => {
                          if (e.target.value === 'duplicate') {
                            handleDuplicate(scenario)
                          } else if (e.target.value === 'delete') {
                            handleDelete(scenario.id, scenario.name)
                          }
                          e.target.value = ''
                        }}
                        defaultValue=""
                      >
                        <option value="" disabled>•••</option>
                        <option value="duplicate">Duplicate</option>
                        <option value="delete">Delete</option>
                      </select>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Modals */}
        {showCreateModal && (
          <CreateScenarioModal
            onClose={() => setShowCreateModal(false)}
            onSuccess={(name) => {
              setShowCreateModal(false)
              addToast({
                type: 'success',
                title: 'Scenario created',
                message: `"${name}" has been created successfully`
              })
              fetchScenarios()
            }}
          />
        )}

        {editingScenario && (
          <EditScenarioModal
            scenario={editingScenario}
            onClose={() => setEditingScenario(null)}
            onSuccess={(name) => {
              setEditingScenario(null)
              addToast({
                type: 'success',
                title: 'Scenario updated',
                message: `"${name}" has been updated successfully`
              })
              fetchScenarios()
            }}
          />
        )}

        {previewingScenario && (
          <ScenarioPreviewModal
            scenario={previewingScenario}
            onClose={() => setPreviewingScenario(null)}
          />
        )}
      </div>
    </div>
  )
}

export default function ScenariosPage() {
  return (
    <ProtectedRoute>
      <ToastProvider>
        <ScenariosPageContent />
      </ToastProvider>
    </ProtectedRoute>
  )
}