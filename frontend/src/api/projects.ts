import request from '@/utils/request'
import type { ApiResponse, PaginatedData } from '@/types/api'

export interface ProjectItem {
  id: string
  name: string
  grade: string
  status: string
  driving_question: string
  lesson_count: number
  objectives: string[]
  owner_name: string
  owner_id: string
  subjects: { id: string; name: string }[]
  classes: { id: string; name: string }[]
  created_at: string
  updated_at: string
}

export interface ProjectCreate {
  name: string
  grade: string
  subject_ids: string[]
  class_ids: string[]
  driving_question: string
  lesson_count: number
  objectives: string[]
}

export function getProjects(
  params?: { page?: number; page_size?: number; status?: string }
): Promise<ApiResponse<PaginatedData<ProjectItem>>> {
  return request.get('/projects', { params })
}

export function getProject(id: string): Promise<ApiResponse<ProjectItem>> {
  return request.get(`/projects/${id}`)
}

export function createProject(
  data: ProjectCreate
): Promise<ApiResponse<ProjectItem>> {
  return request.post('/projects', data)
}

export function updateProject(
  id: string,
  data: Partial<ProjectCreate>
): Promise<ApiResponse<ProjectItem>> {
  return request.patch(`/projects/${id}`, data)
}

export function activateProject(id: string): Promise<ApiResponse<ProjectItem>> {
  return request.post(`/projects/${id}/activate`)
}

export function completeProject(id: string): Promise<ApiResponse<ProjectItem>> {
  return request.post(`/projects/${id}/complete`)
}

export function archiveProject(id: string): Promise<ApiResponse<ProjectItem>> {
  return request.post(`/projects/${id}/archive`)
}
