import Link from 'next/link'
import { Activity, Database, Shield, Target, Play, BarChart3 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Button } from '@/components/ui'
import DashboardCharts from '@/components/dashboard-charts'
import ProtectedRoute from '@/components/protected-route'

export default function Home() {
  return (
    <ProtectedRoute>
      <div className="max-w-7xl mx-auto px-6 space-y-8">
      {/* Hero Section */}
      <div className="text-center py-12">
        <h1 className="text-4xl font-bold mb-4 text-gray-900">
          EvalWise
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Developer-friendly red teaming and evaluation platform for LLMs
        </p>
        <div className="flex justify-center space-x-4">
          <Button asChild>
            <Link href="/playground">Try Playground</Link>
          </Button>
          <Button variant="secondary" asChild>
            <Link href="/runs">View Runs</Link>
          </Button>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <Link href="/datasets">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <Database className="h-8 w-8 text-blue-500 mb-2" />
              <CardTitle>Datasets</CardTitle>
              <CardDescription>
                Upload and manage evaluation datasets with CSV/JSONL support
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/scenarios">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <Target className="h-8 w-8 text-red-500 mb-2" />
              <CardTitle>Scenarios</CardTitle>
              <CardDescription>
                Red teaming scenarios including jailbreaks and safety probes
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/evaluators">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <Shield className="h-8 w-8 text-green-500 mb-2" />
              <CardTitle>Evaluators</CardTitle>
              <CardDescription>
                LLM judges, rule-based checks, and PII detection
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/runs">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <Activity className="h-8 w-8 text-purple-500 mb-2" />
              <CardTitle>Evaluation Runs</CardTitle>
              <CardDescription>
                Execute comprehensive evaluations with detailed results
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Link href="/playground">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardHeader>
              <Play className="h-8 w-8 text-yellow-500 mb-2" />
              <CardTitle>Playground</CardTitle>
              <CardDescription>
                Test single prompts with immediate evaluation results
              </CardDescription>
            </CardHeader>
          </Card>
        </Link>

        <Card>
          <CardHeader>
            <BarChart3 className="h-8 w-8 text-orange-500 mb-2" />
            <CardTitle>Analytics</CardTitle>
            <CardDescription>
              Pass rates, regression analysis, and compliance reporting
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      {/* Dashboard Charts */}
      <DashboardCharts />
      </div>
    </ProtectedRoute>
  )
}