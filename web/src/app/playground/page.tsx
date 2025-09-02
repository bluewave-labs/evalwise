'use client'

import { useState, useEffect } from 'react'
import { Play, Send, AlertTriangle, CheckCircle, Settings } from 'lucide-react'
import Link from 'next/link'
import { playgroundApi, evaluatorApi } from '@/lib/api'

interface Evaluator {
  id: string
  name: string
  kind: string
}

interface EvaluationResult {
  id: string
  evaluator_id: string
  score_float?: number
  pass_bool?: boolean
  notes_text?: string
}

interface PlaygroundResult {
  output: string
  latency_ms: number
  token_input?: number
  token_output?: number
  cost_usd?: number
  evaluations: EvaluationResult[]
}

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState('')
  const [evaluators, setEvaluators] = useState<Evaluator[]>([])
  const [selectedEvaluatorIds, setSelectedEvaluatorIds] = useState<string[]>([])
  const [model, setModel] = useState({
    provider: 'openai',
    name: 'gpt-3.5-turbo',
    params: {
      temperature: 0.7,
      max_tokens: 1000
    }
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PlaygroundResult | null>(null)

  useEffect(() => {
    loadEvaluators()
  }, [])

  const loadEvaluators = async () => {
    try {
      const response = await evaluatorApi.list()
      setEvaluators(response.data)
      // Select a few default evaluators
      const defaultEvaluators = response.data
        .filter((e: Evaluator) => ['rule_based', 'pii_regex'].includes(e.kind))
        .slice(0, 2)
        .map((e: Evaluator) => e.id)
      setSelectedEvaluatorIds(defaultEvaluators)
    } catch (error) {
      console.error('Failed to load evaluators:', error)
    }
  }

  const runTest = async () => {
    if (!prompt.trim()) return
    
    // Validate that at least one evaluator is selected
    if (selectedEvaluatorIds.length === 0) {
      alert('Please select at least one evaluator before running the test.')
      return
    }
    
    setLoading(true)
    setResult(null)
    
    try {
      const response = await playgroundApi.test({
        prompt,
        model,
        evaluator_ids: selectedEvaluatorIds
      })
      setResult(response.data)
    } catch (error) {
      console.error('Failed to run test:', error)
      alert('Test failed. Please check your configuration.')
    } finally {
      setLoading(false)
    }
  }

  const getEvaluationColor = (evaluation: EvaluationResult) => {
    if (evaluation.pass_bool === null || evaluation.pass_bool === undefined) {
      return 'border-gray-600 bg-gray-800'
    }
    return evaluation.pass_bool 
      ? 'border-green-600 bg-green-900/20' 
      : 'border-red-600 bg-red-900/20'
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Playground</h1>
        <p className="text-gray-600 mt-1">Test single prompts with immediate evaluation</p>
      </div>

      {/* Configuration Warnings */}
      {evaluators.length === 0 && (
        <div className="bg-yellow-900/20 border border-yellow-600 rounded-lg p-4 flex items-start space-x-3">
          <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-yellow-300 font-medium">No Evaluators Available</h3>
            <p className="text-yellow-200 text-sm mt-1">
              You don't have any evaluators configured. Evaluators are needed to score and validate your LLM responses.
            </p>
            <Link 
              href="/evaluators" 
              className="inline-flex items-center space-x-1 text-yellow-300 hover:text-yellow-200 text-sm mt-2 underline"
            >
              <Settings className="h-4 w-4" />
              <span>Configure Evaluators</span>
            </Link>
          </div>
        </div>
      )}

      {selectedEvaluatorIds.length === 0 && evaluators.length > 0 && (
        <div className="bg-orange-900/20 border border-orange-600 rounded-lg p-4 flex items-start space-x-3">
          <AlertTriangle className="h-5 w-5 text-orange-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-orange-300 font-medium">No Evaluators Selected</h3>
            <p className="text-orange-200 text-sm mt-1">
              Please select at least one evaluator below to score your prompt responses.
            </p>
          </div>
        </div>
      )}

      {/* Input Section */}
      <div className="bg-white rounded-lg p-6 space-y-4 border border-gray-200">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Prompt
          </label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter your prompt here..."
            className="w-full h-32 bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900 resize-none"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Model Provider
            </label>
            <select
              value={model.provider}
              onChange={(e) => setModel({...model, provider: e.target.value})}
              className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
            >
              <option value="openai">OpenAI</option>
              <option value="azure_openai">Azure OpenAI</option>
              <option value="local_openai">Local OpenAI</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Model Name
            </label>
            <input
              type="text"
              value={model.name}
              onChange={(e) => setModel({...model, name: e.target.value})}
              className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
              placeholder="gpt-3.5-turbo"
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
              value={model.params.temperature}
              onChange={(e) => setModel({
                ...model,
                params: {...model.params, temperature: parseFloat(e.target.value)}
              })}
              className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Evaluators
          </label>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-32 overflow-y-auto">
            {evaluators.map((evaluator) => (
              <label key={evaluator.id} className="flex items-center text-gray-700">
                <input
                  type="checkbox"
                  checked={selectedEvaluatorIds.includes(evaluator.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedEvaluatorIds([...selectedEvaluatorIds, evaluator.id])
                    } else {
                      setSelectedEvaluatorIds(selectedEvaluatorIds.filter(id => id !== evaluator.id))
                    }
                  }}
                  className="mr-2"
                />
                {evaluator.name}
                <span className="ml-2 px-2 py-0.5 bg-gray-200 text-gray-700 text-xs rounded">
                  {evaluator.kind}
                </span>
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={runTest}
          disabled={loading || !prompt.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-3 rounded-lg flex items-center justify-center space-x-2 transition-colors"
        >
          {loading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Running...</span>
            </>
          ) : (
            <>
              <Send className="h-4 w-4" />
              <span>Run Test</span>
            </>
          )}
        </button>
      </div>

      {/* Results Section */}
      {result && (
        <div className="space-y-6">
          {/* Model Response */}
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Model Response</h2>
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <pre className="text-gray-900 whitespace-pre-wrap">{result.output}</pre>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Latency:</span>
                <span className="text-gray-900 ml-2">{result.latency_ms}ms</span>
              </div>
              {result.token_input && (
                <div>
                  <span className="text-gray-600">Input Tokens:</span>
                  <span className="text-gray-900 ml-2">{result.token_input}</span>
                </div>
              )}
              {result.token_output && (
                <div>
                  <span className="text-gray-600">Output Tokens:</span>
                  <span className="text-gray-900 ml-2">{result.token_output}</span>
                </div>
              )}
              {result.cost_usd && (
                <div>
                  <span className="text-gray-600">Cost:</span>
                  <span className="text-gray-900 ml-2">${result.cost_usd.toFixed(4)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Evaluations */}
          <div className="bg-white rounded-lg p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Evaluation Results</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.evaluations.map((evaluation, index) => {
                const evaluator = evaluators.find(e => e.id === evaluation.evaluator_id)
                return (
                  <div
                    key={index}
                    className={`border-2 rounded-lg p-4 ${getEvaluationColor(evaluation)}`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-gray-900">
                        {evaluator?.name || 'Unknown Evaluator'}
                      </h3>
                      <div className="flex items-center space-x-2">
                        {evaluation.pass_bool !== null && evaluation.pass_bool !== undefined && (
                          evaluation.pass_bool ? (
                            <CheckCircle className="h-5 w-5 text-green-400" />
                          ) : (
                            <AlertTriangle className="h-5 w-5 text-red-400" />
                          )
                        )}
                        {evaluation.score_float !== null && evaluation.score_float !== undefined && (
                          <span className="text-gray-900 font-mono">
                            {(evaluation.score_float * 100).toFixed(1)}%
                          </span>
                        )}
                      </div>
                    </div>
                    {evaluation.notes_text && (
                      <p className="text-gray-700 text-sm">{evaluation.notes_text}</p>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Getting Started */}
      {!result && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Getting Started</h2>
          <div className="space-y-3 text-gray-700">
            <p>1. Enter a prompt to test your model against</p>
            <p>2. Configure your model settings (make sure API keys are set)</p>
            <p>3. Select evaluators to run against the response</p>
            <p>4. Click "Run Test" to see results and evaluations</p>
          </div>
          
          <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-600 rounded">
            <p className="text-yellow-300 text-sm">
              <strong>Note:</strong> Make sure your API keys are configured in the backend .env file.
              LLM Judge evaluators require OpenAI API access.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}