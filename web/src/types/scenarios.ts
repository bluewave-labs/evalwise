// Proper TypeScript interfaces for scenarios

export interface ScenarioParams {
  techniques?: string[]
  categories?: string[]
  probe_types?: string[]
  randomize?: boolean
  directness?: 'direct' | 'indirect' | 'gradual'
  approach?: 'direct' | 'indirect' | 'social_engineering'
}

export interface Scenario {
  id: string
  name: string
  type: 'jailbreak_basic' | 'safety_probe' | 'privacy_probe'
  params_json: ScenarioParams
  tags: string[]
  created_at: string
  updated_at: string
}

export interface ScenarioTypeConfig {
  label: string
  icon: React.ComponentType<{ className?: string }>
  color: string
  bgColor: string
  description: string
}

export interface GeneratedAttack {
  id: number
  prompt: string
  technique: string
  category?: string
}

export interface CreateScenarioRequest {
  name: string
  type: string
  params_json: ScenarioParams
  tags: string[]
}

export interface UpdateScenarioRequest {
  name?: string
  params_json?: ScenarioParams
  tags?: string[]
}

export interface ScenarioGenerateRequest {
  base_input: string
  count?: number
}

export interface ScenarioGenerateResponse {
  attacks: GeneratedAttack[]
  total_count: number
}