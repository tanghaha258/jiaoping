import request from '@/utils/request'
import type { ApiResponse } from '@/types/api'

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

export function getDashboardOverview(): Promise<ApiResponse<DashboardOverview>> {
  return request.get('/dashboard/overview')
}

export function getTrialReadiness(): Promise<ApiResponse<TrialReadiness>> {
  return request.get('/dashboard/trial-readiness')
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
