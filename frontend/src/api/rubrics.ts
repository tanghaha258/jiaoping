import request from '@/utils/request'
import type { ApiResponse, PaginatedData } from '@/types/api'

export interface RubricItem {
  id: string
  dimension: string
  weight: number
  levels: { grade?: string; level?: string; description: string }[]
  sort_order: number
}

export interface Rubric {
  id: string
  school_id: string | null
  name: string
  description: string | null
  scope: string
  created_by: string
  creator_name: string | null
  items: RubricItem[]
  created_at: string
  updated_at: string
}

export function getRubrics(
  params?: { page?: number; page_size?: number; scope?: string }
): Promise<ApiResponse<PaginatedData<Rubric>>> {
  return request.get('/rubrics', { params })
}
