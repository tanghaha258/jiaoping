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

export function getDashboardOverview(): Promise<ApiResponse<DashboardOverview>> {
  return request.get('/dashboard/overview')
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
