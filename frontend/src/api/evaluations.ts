import request from '@/utils/request'
import type { ApiResponse, PaginatedData } from '@/types/api'

export interface DimensionScore {
  dimension: string
  score: number
  max_score: number
  comment: string
}

export interface EvaluationItem {
  id: string
  submission_id: string
  evaluator_id: string
  evaluator_name: string
  evaluator_type: string
  rubric_id: string
  rubric_name: string
  scores: Record<string, number>
  /** Computed client-side from scores dict */
  dimension_scores?: DimensionScore[]
  total_score?: number
  max_score?: number
  /** Extended fields from joined data */
  student_name?: string
  student_id?: string
  task_id?: string
  task_title?: string
  comments: string
  status: string
  confirmed_by: string | null
  confirmer_name: string | null
  created_at: string
  updated_at: string
}

export interface EvaluationCreate {
  submission_id: string
  rubric_id: string
  scores: Record<string, number>
  comments: string
  evaluator_type?: string
  /** Alias for scores, for views that use the old format */
  dimension_scores?: DimensionScore[]
}

export function getEvaluations(
  params?: {
    page?: number
    page_size?: number
    submission_id?: string
    evaluator_id?: string
    evaluator_type?: string
    status?: string
  }
): Promise<ApiResponse<PaginatedData<EvaluationItem>>> {
  return request.get('/evaluations', { params })
}

export function getEvaluation(
  id: string
): Promise<ApiResponse<EvaluationItem>> {
  return request.get(`/evaluations/${id}`)
}

export function createEvaluation(
  data: EvaluationCreate
): Promise<ApiResponse<EvaluationItem>> {
  return request.post('/evaluations', data)
}

export function updateEvaluation(
  id: string,
  data: { scores?: Record<string, number>; comments?: string }
): Promise<ApiResponse<EvaluationItem>> {
  return request.patch(`/evaluations/${id}`, data)
}

export function confirmEvaluation(
  id: string
): Promise<ApiResponse<EvaluationItem>> {
  return request.post(`/evaluations/${id}/confirm`)
}

export function getStudentEvaluations(
  params?: { page?: number; page_size?: number }
): Promise<ApiResponse<PaginatedData<EvaluationItem>>> {
  return request.get('/evaluations', { params })
}
