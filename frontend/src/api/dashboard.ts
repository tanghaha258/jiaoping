import request from '@/utils/request'
import type { ApiResponse, PaginatedData } from '@/types/api'

export interface DashboardOverview {
  schools: number
  teachers: number
  students: number
  projects: number
  tasks: number
  resources: number
  ai_calls: number
}

export interface ProjectTrend {
  month: string
  count: number
}

export interface StatusBreakdown {
  status: string
  count: number
}

export interface ProjectTrends {
  by_month: ProjectTrend[]
  by_status: StatusBreakdown[]
}

export type TrialReadinessStatus = 'ready' | 'action_required'
export type TrialReadinessItemStatus = 'ok' | 'warning' | 'error'

export interface TrialReadinessItem {
  key: string
  label: string
  status: TrialReadinessItemStatus
  description: string
  metric: string
  action: string
  route: string
}

export interface TrialReadiness {
  status: TrialReadinessStatus
  checked_at: string
  summary: {
    ok: number
    warning: number
    error: number
  }
  items: TrialReadinessItem[]
}

export interface TrialOperationsStage {
  key: string
  title: string
  status: TrialReadinessItemStatus
  owner: string
  route: string
  primary_action: string
  evidence: string[]
  next_step: string
}

export interface TrialOperationsRunbook {
  status: TrialReadinessStatus
  checked_at: string
  summary: {
    ok: number
    warning: number
    error: number
  }
  stages: TrialOperationsStage[]
}

export type TrialRunbookRecordStatus = 'checked' | 'blocked' | 'skipped'

export interface TrialRunbookRecord {
  id: string
  stage_key: string
  status: TrialRunbookRecordStatus
  note: string
  evidence: string[]
  operator_id: string
  operator_name?: string
  created_at?: string
}

export interface TrialRunbookRecordCreate {
  status: TrialRunbookRecordStatus
  note: string
  evidence: string[]
}

export type TrialDeliveryPackageStatus = 'ready' | 'action_required'

export interface TrialDeliverySummary {
  readiness_ok: number
  readiness_warning: number
  readiness_error: number
  runbook_checked: number
  runbook_blocked: number
  runbook_skipped: number
}

export interface TrialDeliveryAudienceSection {
  key: string
  title: string
  items: string[]
}

export interface TrialDeliveryLatestRecord {
  id: string
  stage_key: string
  status: TrialRunbookRecordStatus
  note: string
  evidence: string[]
  operator_id: string
  operator_name?: string
  created_at?: string
}

export interface TrialDeliveryChecklistItem {
  key: string
  title: string
  status: TrialReadinessItemStatus
  route: string
  owner: string
  primary_action: string
  evidence: string[]
  next_step: string
  latest_record?: TrialDeliveryLatestRecord | null
}

export interface TrialDeliveryDemoStep {
  step: number
  role: string
  title: string
  route: string
  expected_evidence: string
}

export interface TrialDeliveryAccount {
  role: string
  username: string
  password_hint: string
  purpose: string
}

export interface TrialDeliveryPackage {
  status: TrialDeliveryPackageStatus
  generated_at: string
  summary: TrialDeliverySummary
  audience_sections: TrialDeliveryAudienceSection[]
  acceptance_checklist: TrialDeliveryChecklistItem[]
  demo_script: TrialDeliveryDemoStep[]
  accounts: TrialDeliveryAccount[]
  materials: {
    markdown: string
    json: string
  }
}

export function getDashboardOverview(): Promise<ApiResponse<DashboardOverview>> {
  return request.get('/dashboard/overview')
}

export function getTrialReadiness(): Promise<ApiResponse<TrialReadiness>> {
  return request.get('/dashboard/trial-readiness')
}

export function getTrialOperationsRunbook(): Promise<ApiResponse<TrialOperationsRunbook>> {
  return request.get('/dashboard/trial-operations/runbook')
}

export function createTrialRunbookRecord(
  stageKey: string,
  data: TrialRunbookRecordCreate
): Promise<ApiResponse<TrialRunbookRecord>> {
  return request.post(`/dashboard/trial-operations/stages/${stageKey}/records`, data)
}

export function getTrialRunbookRecords(params?: {
  stage_key?: string
  page?: number
  page_size?: number
}): Promise<ApiResponse<PaginatedData<TrialRunbookRecord>>> {
  return request.get('/dashboard/trial-operations/records', { params })
}

export function getTrialDeliveryPackage(): Promise<ApiResponse<TrialDeliveryPackage>> {
  return request.get('/dashboard/trial-delivery/package')
}

export function getProjectTrends(): Promise<ApiResponse<ProjectTrends>> {
  return request.get('/dashboard/project-trends')
}

export interface AIUsage {
  by_scenario: { scenario: string; count: number }[]
  by_provider: { provider: string; count: number }[]
  total_calls: number
}

export function getAIUsage(): Promise<ApiResponse<AIUsage>> {
  return request.get('/dashboard/ai-usage')
}
