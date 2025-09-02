'use client'

import { useState } from 'react'
import { Plus, Trash2, Save, Download, Upload } from 'lucide-react'

interface DatasetRow {
  id: string
  question: string
  context: string
  expectedResponse: string
  topic: string
}

interface DatasetTableEditorProps {
  datasetId?: string
  onSave?: (rows: DatasetRow[]) => Promise<void>
  initialRows?: DatasetRow[]
}

export default function DatasetTableEditor({ 
  datasetId, 
  onSave, 
  initialRows = [] 
}: DatasetTableEditorProps) {
  const [rows, setRows] = useState<DatasetRow[]>(
    initialRows.length > 0 
      ? initialRows 
      : [{
          id: '1',
          question: '',
          context: '',
          expectedResponse: '',
          topic: ''
        }]
  )
  const [saving, setSaving] = useState(false)

  const addRow = () => {
    const newRow: DatasetRow = {
      id: Date.now().toString(),
      question: '',
      context: '',
      expectedResponse: '',
      topic: ''
    }
    setRows([...rows, newRow])
  }

  const deleteRow = (id: string) => {
    if (rows.length > 1) {
      setRows(rows.filter(row => row.id !== id))
    }
  }

  const updateRow = (id: string, field: keyof DatasetRow, value: string) => {
    setRows(rows.map(row => 
      row.id === id ? { ...row, [field]: value } : row
    ))
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      if (onSave) {
        await onSave(rows.filter(row => 
          row.question.trim() || row.context.trim() || row.expectedResponse.trim()
        ))
      }
      alert('Dataset saved successfully!')
    } catch (error) {
      console.error('Failed to save dataset:', error)
      alert('Failed to save dataset')
    } finally {
      setSaving(false)
    }
  }

  const exportToCsv = () => {
    const csvContent = [
      // Header
      'input.question,input.context,expected.response,metadata.topic',
      // Rows
      ...rows.map(row => [
        `"${row.question.replace(/"/g, '""')}"`,
        `"${row.context.replace(/"/g, '""')}"`,
        `"${row.expectedResponse.replace(/"/g, '""')}"`,
        `"${row.topic.replace(/"/g, '""')}"`
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `dataset-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const loadFromCsv = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const csv = e.target?.result as string
        const lines = csv.split('\n')
        const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim())
        
        const newRows: DatasetRow[] = lines.slice(1)
          .filter(line => line.trim())
          .map((line, index) => {
            const values = line.split(',').map(v => v.replace(/"/g, '').trim())
            return {
              id: (Date.now() + index).toString(),
              question: values[0] || '',
              context: values[1] || '',
              expectedResponse: values[2] || '',
              topic: values[3] || ''
            }
          })

        if (newRows.length > 0) {
          setRows(newRows)
        }
      } catch (error) {
        console.error('Failed to parse CSV:', error)
        alert('Failed to parse CSV file')
      }
    }
    reader.readAsText(file)
    
    // Reset file input
    event.target.value = ''
  }

  const fillSampleData = () => {
    const sampleRows: DatasetRow[] = [
      {
        id: '1',
        question: 'What is the capital of France?',
        context: 'This is a basic geography question about European capitals.',
        expectedResponse: 'The capital of France is Paris.',
        topic: 'Geography'
      },
      {
        id: '2',
        question: 'Explain photosynthesis in simple terms.',
        context: 'This question tests understanding of basic biological processes.',
        expectedResponse: 'Photosynthesis is the process by which plants use sunlight, water, and carbon dioxide to create oxygen and energy in the form of sugar.',
        topic: 'Biology'
      },
      {
        id: '3',
        question: 'Write a professional email declining a meeting invitation.',
        context: 'Test the model\'s ability to write professional, courteous communication.',
        expectedResponse: 'Thank you for the meeting invitation. Unfortunately, I have a scheduling conflict and won\'t be able to attend. Could we possibly reschedule for another time that works for everyone?',
        topic: 'Communication'
      }
    ]
    setRows(sampleRows)
  }

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex justify-between items-center bg-gray-50 rounded-lg p-4">
        <div className="flex space-x-2">
          <button
            onClick={addRow}
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-lg flex items-center space-x-2 text-sm"
          >
            <Plus className="h-4 w-4" />
            <span>Add Row</span>
          </button>
          
          <button
            onClick={fillSampleData}
            className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-2 rounded-lg text-sm"
          >
            Sample Data
          </button>
          
          <label className="bg-green-600 hover:bg-green-700 text-white px-3 py-2 rounded-lg flex items-center space-x-2 text-sm cursor-pointer">
            <Upload className="h-4 w-4" />
            <span>Import CSV</span>
            <input
              type="file"
              accept=".csv"
              onChange={loadFromCsv}
              className="hidden"
            />
          </label>
          
          <button
            onClick={exportToCsv}
            className="bg-gray-600 hover:bg-gray-700 text-white px-3 py-2 rounded-lg flex items-center space-x-2 text-sm"
          >
            <Download className="h-4 w-4" />
            <span>Export CSV</span>
          </button>
        </div>

        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
        >
          <Save className="h-4 w-4" />
          <span>{saving ? 'Saving...' : 'Save Dataset'}</span>
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg overflow-hidden border border-gray-200">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="text-left text-gray-900 font-medium p-3 min-w-[200px]">
                  Question/Prompt
                </th>
                <th className="text-left text-gray-900 font-medium p-3 min-w-[200px]">
                  Background Context
                </th>
                <th className="text-left text-gray-900 font-medium p-3 min-w-[250px]">
                  Expected Response
                </th>
                <th className="text-left text-gray-900 font-medium p-3 min-w-[120px]">
                  Topic/Category
                </th>
                <th className="text-left text-gray-900 font-medium p-3 w-16">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={row.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="p-2">
                    <textarea
                      value={row.question}
                      onChange={(e) => updateRow(row.id, 'question', e.target.value)}
                      placeholder="Enter your question or prompt..."
                      className="w-full bg-white border border-gray-200 rounded px-3 py-2 text-gray-900 text-sm resize-none"
                      rows={3}
                    />
                  </td>
                  <td className="p-2">
                    <textarea
                      value={row.context}
                      onChange={(e) => updateRow(row.id, 'context', e.target.value)}
                      placeholder="Provide background context..."
                      className="w-full bg-white border border-gray-200 rounded px-3 py-2 text-gray-900 text-sm resize-none"
                      rows={3}
                    />
                  </td>
                  <td className="p-2">
                    <textarea
                      value={row.expectedResponse}
                      onChange={(e) => updateRow(row.id, 'expectedResponse', e.target.value)}
                      placeholder="What should the ideal response be..."
                      className="w-full bg-white border border-gray-200 rounded px-3 py-2 text-gray-900 text-sm resize-none"
                      rows={3}
                    />
                  </td>
                  <td className="p-2">
                    <input
                      type="text"
                      value={row.topic}
                      onChange={(e) => updateRow(row.id, 'topic', e.target.value)}
                      placeholder="Category..."
                      className="w-full bg-white border border-gray-200 rounded px-3 py-2 text-gray-900 text-sm"
                    />
                  </td>
                  <td className="p-2">
                    <button
                      onClick={() => deleteRow(row.id)}
                      disabled={rows.length === 1}
                      className="p-2 text-gray-600 hover:text-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-gray-900 font-medium mb-2">How it works:</h3>
        <ol className="text-gray-700 text-sm space-y-1 list-decimal list-inside">
          <li>Enter your evaluation questions and expected responses in the table</li>
          <li>Save the dataset and create a new evaluation run</li>
          <li>The target LLM will answer your questions using the provided context</li>
          <li>Evaluator LLMs will compare the responses against your expected outputs</li>
          <li>View detailed results and scoring for each question</li>
        </ol>
      </div>
    </div>
  )
}