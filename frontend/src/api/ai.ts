import request from '@/utils/request'
import type { ApiResponse, PaginatedData } from '@/types/api'
import type { ProjectItem } from './projects'

export interface AIAgent {
  id: string
  name: string
  provider: AIProvider
  scenario: string
  config?: AgentConfig
  input_schema?: Record<string, any>
  output_schema?: Record<string, any>
  enabled: boolean
  agent_type?: string
  description?: string
  is_active?: boolean
  created_at?: string
  updated_at?: string
}

export interface AgentConfig {
  provider?: AIProvider
  model?: string | null
  endpoint?: string | null
  auth_type?: string | null
  api_key_env?: string | null
  timeout_seconds?: number
  max_retries?: number
  extra?: Record<string, any>
}

export type AIProvider =
  | 'gjt_api'
  | 'gjt_link'
  | 'manual_import'
  | 'mock'
  | 'openai_compatible_local'
  | 'qwen_agent'
  | 'deepseek_agent'
  | 'zhipu_agent'
  | 'doubao_agent'
  | 'qianfan_agent'
  | 'spark_agent'
  | 'kimi_agent'

export interface AIAgentMutation {
  name: string
  provider: AIProvider
  scenario: string
  config: AgentConfig
  input_schema?: Record<string, any>
  output_schema?: Record<string, any>
  enabled: boolean
}

export interface AIAgentReadinessCheck {
  key: string
  label: string
  status: 'ok' | 'warning' | 'error'
  message: string
}

export interface AIAgentReadinessAction {
  label: string
  field: string
}

export interface AIAgentReadiness {
  agent_id: string
  provider: string
  status: 'ready' | 'manual_required' | 'not_configured' | 'unsupported'
  mode: string
  label: string
  summary: string
  checks: AIAgentReadinessCheck[]
  actions: AIAgentReadinessAction[]
}

export interface AIContract {
  scenario: string
  name: string
  version: string
  provider_modes: string[]
  input_contract: Record<string, any>
  output_contract: Record<string, any>
  thinking_steps: { code: string; title: string; description?: string; percent: number }[]
  adoption_rule: string
}

export interface AICallProgressStep {
  id: string
  call_id: string
  code: string
  title: string
  description?: string
  status: string
  percent: number
  sort_order: number
  started_at?: string | null
  completed_at?: string | null
  metadata?: Record<string, any>
}

export interface AICallProgress {
  call_id: string
  scenario: string
  status: string
  percent: number
  steps: AICallProgressStep[]
}

export interface AICallItem {
  id: string
  project_id?: string
  agent_id: string
  agent_name?: string
  scenario?: string
  provider?: string
  request_payload?: Record<string, any>
  response_payload?: Record<string, any>
  status: string
  review_status?: string
  error_message?: string | null
  input_summary?: string | null
  output_summary?: string | null
  created_at: string
  updated_at?: string
  call_type?: string
  input_params?: Record<string, any>
  output_content?: string
  adopted_content?: string
}

export interface AICallCreate {
  project_id?: string
  agent_id: string
  scenario: string
  input: Record<string, any>
}

export interface LessonPlanWorkflowOptions {
  subjects: { id: string; name: string }[]
  classes: { id: string; name: string; grade: string }[]
  agents: AIAgent[]
}

export interface LessonPlanDraftRequest {
  agent_id?: string
  theme: string
  grade: string
  subject_ids: string[]
  class_ids: string[]
  lesson_count: number
  core_competencies: string[]
  interdisciplinary_requirements: string
  assessment_preferences: string
  resource_preferences: string
  extra_requirements: string
}

export interface LessonPlanProjectDraft {
  name: string
  grade: string
  subject_ids: string[]
  class_ids: string[]
  driving_question: string
  lesson_count: number
  objectives: string[]
}

export interface LessonPlanTaskDraft {
  title: string
  description: string
  task_type: 'individual' | 'group' | 'classroom' | 'homework'
  submit_type: 'text' | 'file' | 'link' | 'mixed'
}

export interface LessonPlanRubricItemDraft {
  dimension: string
  weight: number
  level_a: string
  level_b: string
  level_c: string
  level_d: string
}

export interface LessonPlanRubricDraft {
  name: string
  description: string
  scope: 'personal' | 'school' | 'region' | 'system'
  items: LessonPlanRubricItemDraft[]
}

export interface LessonPlanResourceDraft {
  title: string
  resource_type: string
  description: string
  suggested_use: string
  url?: string
  visibility: 'personal' | 'school' | 'region' | 'system'
}

export interface LessonPlanDraft {
  project: LessonPlanProjectDraft
  tasks: LessonPlanTaskDraft[]
  rubric: LessonPlanRubricDraft
  resources: LessonPlanResourceDraft[]
  teacher_notes: string[]
}

export interface LessonPlanDraftResponse {
  call_id: string
  status: string
  provider: string
  draft: LessonPlanDraft
}

export interface LessonPlanAdoptResponse {
  call_id: string
  project: ProjectItem
  rubric: { id: string; name: string }
  tasks: { id: string; title: string; status: string }[]
  resources: { id: string; title: string }[]
}

export function getLessonPlanOptions(): Promise<ApiResponse<LessonPlanWorkflowOptions>> {
  return request.get('/ai/workflows/lesson-plan/options')
}

export function createLessonPlanDraft(
  data: LessonPlanDraftRequest
): Promise<ApiResponse<LessonPlanDraftResponse>> {
  return request.post('/ai/workflows/lesson-plan/draft', data)
}

export function adoptLessonPlanDraft(
  callId: string,
  draft: LessonPlanDraft
): Promise<ApiResponse<LessonPlanAdoptResponse>> {
  return request.post(`/ai/workflows/lesson-plan/${callId}/adopt`, { draft })
}

export function getAgents(
  params?: {
    agent_type?: string
    scenario?: string
    provider?: string
    enabled?: boolean
    page?: number
    page_size?: number
  }
): Promise<ApiResponse<PaginatedData<AIAgent>>> {
  const normalizedParams = {
    ...params,
    scenario: params?.scenario || params?.agent_type
  }
  delete (normalizedParams as any).agent_type
  return request.get('/ai/agents', { params: normalizedParams })
}

export function getAIContracts(): Promise<ApiResponse<{ items: AIContract[] }>> {
  return request.get('/ai/contracts')
}

export function getAgent(id: string): Promise<ApiResponse<AIAgent>> {
  return request.get(`/ai/agents/${id}`)
}

export function getAgentReadiness(id: string): Promise<ApiResponse<AIAgentReadiness>> {
  return request.get(`/ai/agents/${id}/readiness`)
}

export function createAgent(
  data: AIAgentMutation
): Promise<ApiResponse<AIAgent>> {
  return request.post('/ai/agents', data)
}

export function updateAgent(
  id: string,
  data: Partial<AIAgentMutation>
): Promise<ApiResponse<AIAgent>> {
  return request.patch(`/ai/agents/${id}`, data)
}

export function deleteAgent(id: string): Promise<ApiResponse<{ id: string; deleted: boolean }>> {
  return request.delete(`/ai/agents/${id}`)
}

export function getAICalls(
  params?: { page?: number; page_size?: number; project_id?: string }
): Promise<ApiResponse<PaginatedData<AICallItem>>> {
  return request.get('/ai/calls', { params })
}

export function getAICall(id: string): Promise<ApiResponse<AICallItem>> {
  return request.get(`/ai/calls/${id}`)
}

export function getAICallProgress(id: string): Promise<ApiResponse<AICallProgress>> {
  return request.get(`/ai/calls/${id}/progress`)
}

export function createAICall(
  data: AICallCreate
): Promise<ApiResponse<AICallItem>> {
  return request.post('/ai/calls', data)
}

export function importResult(
  id: string,
  data: { output_content: Record<string, any> }
): Promise<ApiResponse<AICallItem>> {
  return request.post(`/ai/calls/${id}/import`, data)
}

export function reviewOutput(
  id: string,
  data: { review_status: 'approved' | 'rejected'; modifications?: Record<string, any>; comments?: string }
): Promise<ApiResponse<AICallItem>> {
  return request.post(`/ai/calls/${id}/review`, data)
}

export function adoptOutput(
  id: string,
  data: { target_type: string; target_id?: string | null }
): Promise<ApiResponse<AICallItem>> {
  return request.post(`/ai/calls/${id}/adopt`, data)
}
