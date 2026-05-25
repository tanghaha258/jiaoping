import request from '@/utils/request'
import type { ApiResponse, PaginatedData } from '@/types/api'

export interface TaskItem {
  id: string
  project_id: string
  title: string
  description: string
  task_type: string
  submit_type: string
  status: string
  due_at: string | null
  rubric_id: string | null
  rubric_name: string | null
  submission_count: number
  created_at: string
  updated_at: string
}

export interface SubmissionItem {
  id: string
  task_id: string
  task_title: string
  student_id: string
  student_name: string
  group_name: string
  content: string
  attachments: string[]
  status: string
  submitted_at: string
  evaluation_count: number
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description: string
  task_type: string
  submit_type: string
  due_at: string | null
  rubric_id?: string | null
}

export function getTasks(
  projectId: string,
  params?: { page?: number; page_size?: number; status?: string }
): Promise<ApiResponse<PaginatedData<TaskItem>>> {
  return request.get(`/projects/${projectId}/tasks`, { params })
}

export function getTask(taskId: string): Promise<ApiResponse<TaskItem>> {
  return request.get(`/tasks/${taskId}`)
}

export function createTask(
  projectId: string,
  data: TaskCreate
): Promise<ApiResponse<TaskItem>> {
  return request.post(`/projects/${projectId}/tasks`, data)
}

export function updateTask(
  taskId: string,
  data: Partial<TaskCreate>
): Promise<ApiResponse<TaskItem>> {
  return request.patch(`/tasks/${taskId}`, data)
}

export function publishTask(id: string): Promise<ApiResponse<TaskItem>> {
  return request.post(`/tasks/${id}/publish`)
}

export function closeTask(id: string): Promise<ApiResponse<TaskItem>> {
  return request.post(`/tasks/${id}/close`)
}

export function submitTask(
  taskId: string,
  data: { content: string; group_name?: string }
): Promise<ApiResponse<SubmissionItem>> {
  return request.post(`/tasks/${taskId}/submissions`, data)
}

export function getSubmissions(
  taskId: string,
  params?: { page?: number; page_size?: number; status?: string }
): Promise<ApiResponse<PaginatedData<SubmissionItem>>> {
  return request.get(`/tasks/${taskId}/submissions`, { params })
}

export function getSubmission(
  id: string
): Promise<ApiResponse<SubmissionItem>> {
  return request.get(`/submissions/${id}`)
}

export function getTasksForStudent(
  params?: { page?: number; page_size?: number; status?: string }
): Promise<ApiResponse<PaginatedData<TaskItem>>> {
  return request.get('/student/tasks', { params })
}

export function getSubmissionsForStudent(
  params?: { page?: number; page_size?: number }
): Promise<ApiResponse<PaginatedData<SubmissionItem>>> {
  return request.get('/student/submissions', { params })
}
