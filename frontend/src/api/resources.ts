import request from '@/utils/request'
import type { ApiResponse, PaginatedData } from '@/types/api'

export interface ResourceItem {
  id: string
  school_id: string | null
  title: string
  resource_type: string
  file_path: string | null
  url: string | null
  metadata: Record<string, any> | null
  visibility: string
  status: string
  created_at: string
  updated_at: string
}

export interface ResourceMutation {
  title: string
  resource_type: string
  file_path?: string | null
  url?: string | null
  metadata?: Record<string, any> | null
  visibility: 'personal' | 'school' | 'region' | 'system'
}

export function getResources(
  params?: { page?: number; page_size?: number; resource_type?: string; visibility?: string }
): Promise<ApiResponse<PaginatedData<ResourceItem>>> {
  return request.get('/resources', { params })
}

export function getResource(id: string): Promise<ApiResponse<ResourceItem>> {
  return request.get(`/resources/${id}`)
}

export function createResource(
  data: ResourceMutation
): Promise<ApiResponse<ResourceItem>> {
  return request.post('/resources', data)
}

export function updateResource(
  id: string,
  data: Partial<ResourceMutation>
): Promise<ApiResponse<ResourceItem>> {
  return request.patch(`/resources/${id}`, data)
}

export function deleteResource(id: string): Promise<ApiResponse<ResourceItem>> {
  return request.delete(`/resources/${id}`)
}
