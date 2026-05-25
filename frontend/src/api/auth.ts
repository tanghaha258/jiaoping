import request from '@/utils/request'
import type {
  LoginRequest,
  LoginResponse,
  RefreshTokenResponse,
  ApiResponse,
  UserInfo
} from '@/types/api'

export function login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
  return request.post('/auth/login', data)
}

export function refreshToken(token: string): Promise<ApiResponse<RefreshTokenResponse>> {
  return request.post('/auth/refresh', { refresh_token: token })
}

export function logout(): Promise<ApiResponse<null>> {
  return request.post('/auth/logout')
}

export function getCurrentUser(): Promise<ApiResponse<UserInfo>> {
  return request.get('/auth/me')
}

export function changePassword(data: {
  current_password: string
  new_password: string
}): Promise<ApiResponse<{ updated: boolean }>> {
  return request.post('/auth/change-password', data)
}
