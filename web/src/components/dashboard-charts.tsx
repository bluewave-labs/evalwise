"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, BarChart, PieChart } from '@/components/ui'
import { Activity, Database, Target, Shield, TrendingUp, Clock, AlertTriangle, CheckCircle } from 'lucide-react'
import { dashboardApi } from '@/lib/api'

interface DashboardMetrics {
  totals: {
    datasets: number
    scenarios: number
    evaluators: number
    runs: number
    recent_runs: number
  }
  run_status: {
    pending: number
    running: number
    completed: number
    failed: number
  }
  recent_evaluations: {
    passed: number
    failed: number
    total: number
  }
  pass_rates_by_category: { [key: string]: number }
  active_datasets: { name: string, runs: number }[]
}

export default function DashboardCharts() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchMetrics()
  }, [])

  const fetchMetrics = async () => {
    try {
      const response = await dashboardApi.getMetrics()
      setMetrics(response.data)
    } catch (err: any) {
      console.error('Failed to fetch metrics:', err)
      setError('Failed to load dashboard metrics')
      // Use sample data as fallback
      setMetrics({
        totals: { datasets: 5, scenarios: 8, evaluators: 6, runs: 12, recent_runs: 8 },
        run_status: { pending: 2, running: 1, completed: 8, failed: 1 },
        recent_evaluations: { passed: 156, failed: 32, total: 188 },
        pass_rates_by_category: {
          'safety': 85.2,
          'pii': 92.1,
          'toxicity': 78.5,
          'jailbreak': 88.9
        },
        active_datasets: [
          { name: 'Safety Test Suite', runs: 5 },
          { name: 'PII Detection Tests', runs: 3 },
          { name: 'Jailbreak Scenarios', runs: 2 }
        ]
      })
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Card key={i}>
              <CardHeader className="animate-pulse">
                <div className="h-4 bg-muted rounded w-20"></div>
                <div className="h-8 bg-muted rounded w-12"></div>
              </CardHeader>
            </Card>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card><CardContent className="h-64 animate-pulse bg-muted"></CardContent></Card>
          <Card><CardContent className="h-64 animate-pulse bg-muted"></CardContent></Card>
        </div>
      </div>
    )
  }

  if (!metrics) return null

  // Prepare chart data
  const passRateLabels = Object.keys(metrics.pass_rates_by_category)
  const passRateData = {
    labels: passRateLabels.map(key => key.charAt(0).toUpperCase() + key.slice(1)),
    datasets: [
      {
        label: 'Pass Rate (%)',
        data: Object.values(metrics.pass_rates_by_category),
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)', // green
          'rgba(59, 130, 246, 0.8)', // blue
          'rgba(239, 68, 68, 0.8)',  // red
          'rgba(245, 158, 11, 0.8)', // yellow
          'rgba(168, 85, 247, 0.8)', // purple
          'rgba(236, 72, 153, 0.8)', // pink
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)', 
          'rgba(239, 68, 68, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(168, 85, 247, 1)',
          'rgba(236, 72, 153, 1)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const runStatusData = {
    labels: ['Completed', 'Failed', 'Running', 'Pending'],
    datasets: [
      {
        data: [
          metrics.run_status.completed,
          metrics.run_status.failed,
          metrics.run_status.running,
          metrics.run_status.pending
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)', // green
          'rgba(239, 68, 68, 0.8)',  // red
          'rgba(59, 130, 246, 0.8)', // blue
          'rgba(156, 163, 175, 0.8)', // gray
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(156, 163, 175, 1)',
        ],
        borderWidth: 1,
      },
    ],
  }

  const passRate = metrics.recent_evaluations.total > 0 
    ? ((metrics.recent_evaluations.passed / metrics.recent_evaluations.total) * 100).toFixed(1)
    : '0'

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 text-sm text-yellow-800 bg-yellow-50 border border-yellow-200 rounded">
          {error} - Showing sample data
        </div>
      )}
      
      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Datasets</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totals.datasets}</div>
            <p className="text-xs text-muted-foreground">
              Ready for evaluation
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Evaluation Runs</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.totals.runs}</div>
            <p className="text-xs text-muted-foreground">
              +{metrics.totals.recent_runs} this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pass Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{passRate}%</div>
            <p className="text-xs text-muted-foreground">
              Last 7 days ({metrics.recent_evaluations.total} evals)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Runs</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{metrics.run_status.running + metrics.run_status.pending}</div>
            <p className="text-xs text-muted-foreground">
              {metrics.run_status.running} running, {metrics.run_status.pending} pending
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Evaluation Pass Rates by Category</CardTitle>
            <CardDescription>
              Performance across different evaluation types (last 7 days)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {passRateLabels.length > 0 ? (
              <div className="h-64">
                <BarChart 
                  data={passRateData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                          callback: (value: any) => `${value}%`,
                        },
                      },
                    },
                    plugins: {
                      legend: {
                        display: false,
                      },
                    },
                  }}
                />
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-muted-foreground">
                No evaluation data available yet
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Run Status Distribution</CardTitle>
            <CardDescription>
              Current state of all evaluation runs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <PieChart 
                data={runStatusData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom' as const,
                    },
                  },
                }}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Most Active Datasets */}
      {metrics.active_datasets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Most Active Datasets</CardTitle>
            <CardDescription>
              Datasets with the most evaluation runs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {metrics.active_datasets.map((dataset, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Database className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{dataset.name}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-muted-foreground">{dataset.runs} runs</span>
                    <div className="w-20 bg-muted h-2 rounded-full">
                      <div 
                        className="h-2 bg-primary rounded-full" 
                        style={{ width: `${Math.min((dataset.runs / Math.max(...metrics.active_datasets.map(d => d.runs))) * 100, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}