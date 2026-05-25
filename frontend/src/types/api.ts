// Standard API response
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  trace_id: string
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

// User & Auth types
export interface UserInfo {
  id: string
  username: string
  name: string
  role: UserRole
  school_id: string | null
  school_name?: string
  class_id?: string | null
}

export type UserRole =
  | 'system_admin'
  | 'region_admin'
  | 'school_admin'
  | 'researcher'
  | 'teacher'
  | 'student'
  | 'parent'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}

export interface RefreshTokenResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}
