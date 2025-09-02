import Link from 'next/link'
import { Activity, Database, Shield, Target, Play, BarChart3 } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, Button } from '@/components/ui'
import DashboardCharts from '@/components/dashboard-charts'
import ProtectedRoute from '@/components/protected-route'

export default function Home() {
  return (
    <ProtectedRoute>
      <div className="space-y-8">
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

      {/* Built-in Evaluators */}
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">Built-in Evaluators & Scenarios</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4">🔍 Evaluators</h3>
              <ul className="space-y-2 text-gray-600">
                <li>• LLM Judge with ISO 42001 AI Management rubric</li>
                <li>• LLM Judge with EU AI Act compliance rubric</li>
                <li>• Rule-based safety filtering (regex, blocklists)</li>
                <li>• PII detection (email, phone, SSN, credit cards)</li>
                <li>• Exact match and semantic similarity</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">🎯 Red Team Scenarios</h3>
              <ul className="space-y-2 text-gray-600">
                <li>• Basic jailbreaks (DAN, roleplay, hypothetical)</li>
                <li>• Safety boundary testing (violence, hate, harm)</li>
                <li>• Privacy information extraction attempts</li>
                <li>• System prompt extraction techniques</li>
                <li>• Multi-turn conversation attacks</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Start */}
      <Card className="border-primary/20">
        <CardHeader>
          <CardTitle>Quick Start</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-gray-600 mb-6">
            <p>1. Upload a dataset or use the demo data</p>
            <p>2. Select red teaming scenarios and evaluators</p>
            <p>3. Configure your model settings (OpenAI, Azure, local)</p>
            <p>4. Run evaluation and analyze results</p>
          </div>
          
          <div className="flex space-x-4">
            <Button variant="outline" asChild>
              <Link href="/datasets">Upload Dataset →</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link href="/playground">Try Playground →</Link>
            </Button>
          </div>
        </CardContent>
      </Card>
      </div>
    </ProtectedRoute>
  )
}