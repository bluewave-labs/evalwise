'use client'

import { useState, useEffect } from 'react'
import { Play, Plus, Clock, CheckCircle, XCircle, Activity, Settings, Key, Bot } from 'lucide-react'
import { runApi, datasetApi, scenarioApi, evaluatorApi } from '@/lib/api'
import Link from 'next/link'

interface Run {
  id: string
  name: string
  dataset_id: string
  scenario_ids: string[]
  model_provider: string
  model_name: string
  started_at: string
  finished_at?: string
  status: string
}

interface Dataset {
  id: string
  name: string
}

interface Scenario {
  id: string
  name: string
  type: string
}

interface Evaluator {
  id: string
  name: string
  kind: string
}

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

export default function RunsPage() {
  const [runs, setRuns] = useState<Run[]>([])
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [evaluators, setEvaluators] = useState<Evaluator[]>([])
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  
  const [newRun, setNewRun] = useState({
    name: '',
    dataset_id: '',
    scenario_ids: [] as string[],
    evaluator_ids: [] as string[],
    // Target LLM configuration
    target_provider_id: '',
    target_model_name: '',
    target_temperature: 0.7,
    target_max_tokens: 1000,
    // Evaluator LLM configuration
    evaluator_provider_id: '',
    evaluator_model_name: '',
    evaluator_temperature: 0.1,
    evaluator_max_tokens: 500
  })
  const [executingRuns, setExecutingRuns] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      // Load each endpoint separately with error handling
      const results = await Promise.allSettled([
        runApi.list().catch(err => {
          console.error('Failed to load runs:', err)
          return { data: [] }
        }),
        datasetApi.list().catch(err => {
          console.error('Failed to load datasets:', err)
          return { data: [] }
        }),
        scenarioApi.list().catch(err => {
          console.error('Failed to load scenarios:', err)
          return { data: [] }
        }),
        evaluatorApi.list().catch(err => {
          console.error('Failed to load evaluators:', err)
          return { data: [] }
        })
      ])
      
      // Extract successful results
      const [runsRes, datasetsRes, scenariosRes, evaluatorsRes] = results.map(result => 
        result.status === 'fulfilled' ? result.value : { data: [] }
      )
      
      // Load providers from localStorage for now
      const savedProviders = localStorage.getItem('evalwise_providers')
      if (savedProviders) {
        setProviders(JSON.parse(savedProviders))
      }
      
      setRuns(runsRes.data || [])
      setDatasets(datasetsRes.data || [])
      setScenarios(scenariosRes.data || [])
      setEvaluators(evaluatorsRes.data || [])
    } catch (error) {
      console.error('Failed to load data:', error)
      // Set empty arrays as fallback
      setRuns([])
      setDatasets([])
      setScenarios([])
      setEvaluators([])
    } finally {
      setLoading(false)
    }
  }

  const createRun = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await runApi.create(newRun)
      setShowCreateForm(false)
      setNewRun({
        name: '',
        dataset_id: '',
        scenario_ids: [],
        evaluator_ids: [],
        target_provider_id: '',
        target_model_name: '',
        target_temperature: 0.7,
        target_max_tokens: 1000,
        evaluator_provider_id: '',
        evaluator_model_name: '',
        evaluator_temperature: 0.1,
        evaluator_max_tokens: 500
      })
      loadData()
    } catch (error) {
      console.error('Failed to create run:', error)
      alert('Failed to create run')
    }
  }

  const executeRun = async (runId: string) => {
    setExecutingRuns(prev => new Set([...prev, runId]))
    
    try {
      await runApi.execute(runId)
      alert('Run started successfully!')
      await loadData()
    } catch (error: any) {
      console.error('Failed to execute run:', error)
      alert('Failed to start run: ' + (error.response?.data?.detail || 'Unknown error'))
    } finally {
      setExecutingRuns(prev => {
        const newSet = new Set(prev)
        newSet.delete(runId)
        return newSet
      })
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="h-5 w-5 text-yellow-400" />
      case 'running':
        return <Activity className="h-5 w-5 text-blue-400 animate-pulse" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-400" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-400" />
      default:
        return <Clock className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-600 text-yellow-100'
      case 'running':
        return 'bg-blue-600 text-blue-100'
      case 'completed':
        return 'bg-green-600 text-green-100'
      case 'failed':
        return 'bg-red-600 text-red-100'
      default:
        return 'bg-gray-600 text-gray-100'
    }
  }

  const handleTargetProviderChange = (providerId: string) => {
    const provider = providers.find(p => p.id === providerId)
    setNewRun({
      ...newRun,
      target_provider_id: providerId,
      target_model_name: provider?.model_defaults.model_name || '',
      target_temperature: provider?.model_defaults.temperature || 0.7,
      target_max_tokens: provider?.model_defaults.max_tokens || 1000
    })
  }

  const handleEvaluatorProviderChange = (providerId: string) => {
    const provider = providers.find(p => p.id === providerId)
    setNewRun({
      ...newRun,
      evaluator_provider_id: providerId,
      evaluator_model_name: provider?.model_defaults.model_name || '',
      evaluator_temperature: provider?.model_defaults.temperature || 0.1,
      evaluator_max_tokens: provider?.model_defaults.max_tokens || 500
    })
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
          <h1 className="text-3xl font-bold text-gray-900">Evaluation Runs</h1>
          <p className="text-gray-600 mt-1">Execute and monitor evaluation runs</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
        >
          <Plus className="h-4 w-4" />
          <span>New Run</span>
        </button>
      </div>

      {/* Create Run Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Create New Evaluation Run</h2>
          
          {providers.length === 0 && (
            <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-2">
                <Key className="h-5 w-5 text-yellow-400" />
                <h3 className="text-yellow-300 font-medium">No LLM Providers Configured</h3>
              </div>
              <p className="text-yellow-200 text-sm mt-2">
                You need to configure LLM providers before creating evaluation runs.
              </p>
              <Link href="/providers" className="inline-flex items-center space-x-2 mt-3 text-yellow-300 hover:text-yellow-100 text-sm">
                <Settings className="h-4 w-4" />
                <span>Configure Providers</span>
              </Link>
            </div>
          )}
          
          <form onSubmit={createRun} className="space-y-6">
            {/* Basic Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Run Name (optional)
                </label>
                <input
                  type="text"
                  value={newRun.name}
                  onChange={(e) => setNewRun({...newRun, name: e.target.value})}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                  placeholder="My evaluation run"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dataset *
                </label>
                <select
                  value={newRun.dataset_id}
                  onChange={(e) => setNewRun({...newRun, dataset_id: e.target.value})}
                  className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                  required
                >
                  <option value="">Select dataset</option>
                  {datasets.map((dataset) => (
                    <option key={dataset.id} value={dataset.id}>
                      {dataset.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Scenarios */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Scenarios *
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-32 overflow-y-auto bg-gray-50 p-3 rounded-lg border border-gray-300">
                {scenarios.map((scenario) => (
                  <label key={scenario.id} className="flex items-center text-gray-700 hover:text-gray-900 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newRun.scenario_ids.includes(scenario.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewRun({
                            ...newRun,
                            scenario_ids: [...newRun.scenario_ids, scenario.id]
                          })
                        } else {
                          setNewRun({
                            ...newRun,
                            scenario_ids: newRun.scenario_ids.filter(id => id !== scenario.id)
                          })
                        }
                      }}
                      className="mr-2"
                    />
                    {scenario.name}
                  </label>
                ))}
              </div>
            </div>

            {/* Evaluators */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Evaluators *
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-32 overflow-y-auto bg-gray-50 p-3 rounded-lg border border-gray-300">
                {evaluators.map((evaluator) => (
                  <label key={evaluator.id} className="flex items-center text-gray-700 hover:text-gray-900 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={newRun.evaluator_ids.includes(evaluator.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setNewRun({
                            ...newRun,
                            evaluator_ids: [...newRun.evaluator_ids, evaluator.id]
                          })
                        } else {
                          setNewRun({
                            ...newRun,
                            evaluator_ids: newRun.evaluator_ids.filter(id => id !== evaluator.id)
                          })
                        }
                      }}
                      className="mr-2"
                    />
                    {evaluator.name}
                  </label>
                ))}
              </div>
            </div>

            {/* Target LLM Configuration */}
            <div className="bg-blue-900/10 border border-blue-700 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-3">
                <Bot className="h-5 w-5 text-blue-400" />
                <h3 className="text-blue-300 font-medium">Target LLM</h3>
                <span className="text-gray-600 text-sm">(Generates responses)</span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Provider *
                  </label>
                  <select
                    value={newRun.target_provider_id}
                    onChange={(e) => handleTargetProviderChange(e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                    required
                  >
                    <option value="">Select provider</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {getProviderIcon(provider.provider_type)} {provider.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model *
                  </label>
                  <input
                    type="text"
                    value={newRun.target_model_name}
                    onChange={(e) => setNewRun({...newRun, target_model_name: e.target.value})}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                    placeholder="gpt-3.5-turbo, gpt-4, llama2:7b"
                    required
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Temperature
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={newRun.target_temperature}
                    onChange={(e) => setNewRun({...newRun, target_temperature: parseFloat(e.target.value)})}
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
                    value={newRun.target_max_tokens}
                    onChange={(e) => setNewRun({...newRun, target_max_tokens: parseInt(e.target.value)})}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                  />
                </div>
              </div>
            </div>

            {/* Evaluator LLM Configuration */}
            <div className="bg-purple-900/10 border border-purple-700 rounded-lg p-4">
              <div className="flex items-center space-x-2 mb-3">
                <Activity className="h-5 w-5 text-purple-400" />
                <h3 className="text-purple-300 font-medium">Evaluator LLM</h3>
                <span className="text-gray-600 text-sm">(Scores responses)</span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Provider *
                  </label>
                  <select
                    value={newRun.evaluator_provider_id}
                    onChange={(e) => handleEvaluatorProviderChange(e.target.value)}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                    required
                  >
                    <option value="">Select provider</option>
                    {providers.map((provider) => (
                      <option key={provider.id} value={provider.id}>
                        {getProviderIcon(provider.provider_type)} {provider.name}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Model *
                  </label>
                  <input
                    type="text"
                    value={newRun.evaluator_model_name}
                    onChange={(e) => setNewRun({...newRun, evaluator_model_name: e.target.value})}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                    placeholder="gpt-3.5-turbo, gpt-4, llama2:7b"
                    required
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Temperature
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="2"
                    step="0.1"
                    value={newRun.evaluator_temperature}
                    onChange={(e) => setNewRun({...newRun, evaluator_temperature: parseFloat(e.target.value)})}
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
                    max="4000"
                    value={newRun.evaluator_max_tokens}
                    onChange={(e) => setNewRun({...newRun, evaluator_max_tokens: parseInt(e.target.value)})}
                    className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                * Target LLM generates responses, Evaluator LLM scores them
              </div>
              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={providers.length === 0}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg"
                >
                  Create Run
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Runs List */}
      <div className="space-y-4">
        {runs.map((run) => {
          const dataset = datasets.find(d => d.id === run.dataset_id)
          
          return (
            <div key={run.id} className="bg-white rounded-lg p-6 border border-gray-200">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center space-x-3 mb-2">
                    {getStatusIcon(run.status)}
                    <h3 className="text-lg font-semibold text-gray-900">
                      {run.name || 'Unnamed Run'}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded ${getStatusColor(run.status)}`}>
                      {run.status}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-700">
                    <div>
                      <strong>Dataset:</strong> {dataset?.name || 'Unknown'}
                    </div>
                    <div>
                      <strong>Model:</strong> {run.model_provider}/{run.model_name}
                    </div>
                    <div>
                      <strong>Created:</strong> {new Date(run.started_at).toLocaleString()}
                    </div>
                  </div>
                </div>
                <div className="flex space-x-2">
                  {run.status === 'pending' && (
                    <button
                      onClick={() => executeRun(run.id)}
                      disabled={executingRuns.has(run.id)}
                      className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-3 py-1 rounded text-sm flex items-center space-x-1"
                    >
                      {executingRuns.has(run.id) ? (
                        <>
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white mr-1"></div>
                          Starting...
                        </>
                      ) : (
                        <>
                          <Play className="h-3 w-3" />
                          <span>Execute</span>
                        </>
                      )}
                    </button>
                  )}
                  
                  <button className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm">
                    View Details
                  </button>
                  
                  {run.status === 'completed' && (
                    <button className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-sm">
                      Results
                    </button>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {runs.length === 0 && (
        <div className="text-center py-12">
          <Play className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No runs yet</h3>
          <p className="text-gray-600 mb-4">Create your first evaluation run</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Create Run
          </button>
        </div>
      )}
    </div>
  )
}