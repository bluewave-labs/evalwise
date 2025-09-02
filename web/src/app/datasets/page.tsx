'use client'

import { useState, useEffect } from 'react'
import { Upload, Plus, Database, FileText, Table, ChevronLeft } from 'lucide-react'
import { datasetApi } from '@/lib/api'
import DatasetTableEditor from '@/components/dataset-table-editor'

interface Dataset {
  id: string
  name: string
  version_hash: string
  tags: string[]
  is_synthetic: boolean
  created_at: string
  item_count?: number
}

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [showTableEditor, setShowTableEditor] = useState(false)
  const [editingDataset, setEditingDataset] = useState<Dataset | null>(null)
  const [newDataset, setNewDataset] = useState<{
    name: string
    tags: string[]
    is_synthetic: boolean
  }>({
    name: '',
    tags: [],
    is_synthetic: false
  })
  const [uploadingDatasets, setUploadingDatasets] = useState<Set<string>>(new Set())
  const [uploadStatus, setUploadStatus] = useState<{[key: string]: string}>({})

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const response = await datasetApi.list()
      setDatasets(response.data)
    } catch (error) {
      console.error('Failed to load datasets:', error)
    } finally {
      setLoading(false)
    }
  }

  const createDataset = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await datasetApi.create(newDataset)
      setShowCreateForm(false)
      setNewDataset({ name: '', tags: [], is_synthetic: false })
      loadDatasets()
      return response.data // Return dataset for table editor use
    } catch (error) {
      console.error('Failed to create dataset:', error)
      throw error
    }
  }

  const handleCreateWithTable = async () => {
    try {
      // Create a basic dataset first
      const dataset = await createDataset(new Event('submit') as any)
      setEditingDataset(dataset)
      setShowTableEditor(true)
    } catch (error) {
      console.error('Failed to create dataset for table editing:', error)
    }
  }

  const handleTableEditorSave = async (rows: any[]) => {
    if (!editingDataset) return
    
    try {
      // Convert table rows to CSV format for upload
      const csvContent = [
        'input.question,input.context,expected.response,metadata.topic',
        ...rows.map(row => [
          `"${row.question.replace(/"/g, '""')}"`,
          `"${row.context.replace(/"/g, '""')}"`,
          `"${row.expectedResponse.replace(/"/g, '""')}"`,
          `"${row.topic.replace(/"/g, '""')}"`
        ].join(','))
      ].join('\n')
      
      const blob = new Blob([csvContent], { type: 'text/csv' })
      const file = new File([blob], 'dataset.csv', { type: 'text/csv' })
      
      await handleFileUpload(editingDataset.id, file)
      setShowTableEditor(false)
      setEditingDataset(null)
    } catch (error) {
      console.error('Failed to save dataset from table:', error)
      alert('Failed to save dataset')
    }
  }

  const handleFileUpload = async (datasetId: string, file: File) => {
    // Add to uploading set
    setUploadingDatasets(prev => new Set([...prev, datasetId]))
    setUploadStatus(prev => ({...prev, [datasetId]: 'Uploading...'}))
    
    try {
      const response = await datasetApi.uploadItems(datasetId, file)
      setUploadStatus(prev => ({
        ...prev, 
        [datasetId]: `✅ Uploaded ${response.data.items_created} items`
      }))
      
      // Reload datasets to get updated counts
      await loadDatasets()
      
      // Clear status after 3 seconds
      setTimeout(() => {
        setUploadStatus(prev => {
          const newStatus = {...prev}
          delete newStatus[datasetId]
          return newStatus
        })
      }, 3000)
      
    } catch (error: any) {
      console.error('Failed to upload file:', error)
      const errorMessage = error.response?.data?.detail || 'Upload failed'
      setUploadStatus(prev => ({...prev, [datasetId]: `❌ ${errorMessage}`}))
      
      // Clear error after 5 seconds
      setTimeout(() => {
        setUploadStatus(prev => {
          const newStatus = {...prev}
          delete newStatus[datasetId]
          return newStatus
        })
      }, 5000)
    } finally {
      // Remove from uploading set
      setUploadingDatasets(prev => {
        const newSet = new Set(prev)
        newSet.delete(datasetId)
        return newSet
      })
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
          <h1 className="text-3xl font-bold text-gray-900">Datasets</h1>
          <p className="text-gray-600 mt-1">Manage evaluation datasets</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
          >
            <Plus className="h-4 w-4" />
            <span>Upload CSV</span>
          </button>
          <button
            onClick={() => {
              setNewDataset({ name: 'New Dataset', tags: [], is_synthetic: false })
              handleCreateWithTable()
            }}
            className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
          >
            <Table className="h-4 w-4" />
            <span>Create with Table</span>
          </button>
        </div>
      </div>

      {/* Create Dataset Form */}
      {showCreateForm && (
        <div className="bg-white rounded-lg p-6 border border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Create New Dataset</h2>
          <form onSubmit={createDataset} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                type="text"
                value={newDataset.name}
                onChange={(e) => setNewDataset({...newDataset, name: e.target.value})}
                className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                onChange={(e) => setNewDataset({
                  ...newDataset, 
                  tags: e.target.value.split(',').map(t => t.trim()).filter(t => t)
                })}
                className="w-full bg-white border border-gray-300 rounded-lg px-3 py-2 text-gray-900"
                placeholder="demo, qa, safety"
              />
            </div>
            <div>
              <label className="flex items-center text-gray-700">
                <input
                  type="checkbox"
                  checked={newDataset.is_synthetic}
                  onChange={(e) => setNewDataset({...newDataset, is_synthetic: e.target.checked})}
                  className="mr-2"
                />
                Synthetic dataset
              </label>
            </div>
            <div className="flex space-x-3">
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Create
              </button>
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Table Editor */}
      {showTableEditor && editingDataset && (
        <div className="space-y-4">
          <div className="flex items-center justify-between bg-white rounded-lg p-4 border border-gray-200">
            <div className="flex items-center space-x-3">
              <button
                onClick={() => {
                  setShowTableEditor(false)
                  setEditingDataset(null)
                }}
                className="text-gray-600 hover:text-gray-900"
              >
                <ChevronLeft className="h-5 w-5" />
              </button>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Edit Dataset: {editingDataset.name}</h2>
                <p className="text-gray-600 text-sm">Add evaluation questions, contexts, and expected responses</p>
              </div>
            </div>
          </div>
          
          <DatasetTableEditor 
            datasetId={editingDataset.id}
            onSave={handleTableEditorSave}
          />
        </div>
      )}

      {/* Datasets Grid */}
      {!showTableEditor && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets.map((dataset) => (
          <div key={dataset.id} className="bg-white rounded-lg p-6 border border-gray-200">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Database className="h-5 w-5 text-blue-400" />
                <h3 className="font-semibold text-gray-900">{dataset.name}</h3>
              </div>
              {dataset.is_synthetic && (
                <span className="px-2 py-1 bg-yellow-600 text-yellow-100 text-xs rounded">
                  Synthetic
                </span>
              )}
            </div>
            
            <div className="space-y-2 text-sm text-gray-700 mb-4">
              <p>Version: {dataset.version_hash.slice(0, 8)}</p>
              <p>Created: {new Date(dataset.created_at).toLocaleDateString()}</p>
              {dataset.item_count !== undefined && (
                <p>Items: {dataset.item_count}</p>
              )}
              {dataset.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {dataset.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-2">
              {/* Upload Status */}
              {uploadStatus[dataset.id] && (
                <div className="text-center text-sm py-2">
                  {uploadStatus[dataset.id]}
                </div>
              )}
              
              <label className="block">
                <input
                  type="file"
                  accept=".csv,.jsonl"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) handleFileUpload(dataset.id, file)
                  }}
                  className="hidden"
                  disabled={uploadingDatasets.has(dataset.id)}
                />
                <span className={`flex items-center justify-center w-full px-3 py-2 rounded-lg transition-colors ${
                  uploadingDatasets.has(dataset.id)
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700 cursor-pointer'
                }`}>
                  {uploadingDatasets.has(dataset.id) ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload CSV
                    </>
                  )}
                </span>
              </label>
              
              <button 
                onClick={() => {
                  setEditingDataset(dataset)
                  setShowTableEditor(true)
                }}
                className="flex items-center justify-center w-full px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <Table className="h-4 w-4 mr-2" />
                Edit with Table
              </button>
              
              <button className="flex items-center justify-center w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                <FileText className="h-4 w-4 mr-2" />
                View Details
              </button>
            </div>
          </div>
          ))}
        </div>
      )}

      {!showTableEditor && datasets.length === 0 && (
        <div className="text-center py-12">
          <Database className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No datasets yet</h3>
          <p className="text-gray-600 mb-4">Create your first dataset to get started</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Create Dataset
          </button>
        </div>
      )}
    </div>
  )
}