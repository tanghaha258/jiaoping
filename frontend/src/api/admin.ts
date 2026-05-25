import request from '@/utils/request'
import type { ApiResponse, PaginatedData, UserRole } from '@/types/api'
import type { AICallItem } from './ai'

export interface AdminUserItem {
  id: string
  username: string
  name: string
  role: UserRole
  school_id: string | null
  school_name?: string | null
  class_id?: string | null
  status: string
  last_login_at?: string | null
  created_at?: string | null
}

export interface AdminUserCreate {
  username: string
  password: string
  name: string
  role: UserRole
  school_id?: string | null
  class_id?: string | null
}

export interface AdminUserUpdate {
  name?: string
  role?: UserRole
  school_id?: string | null
  class_id?: string | null
  status?: string
}

export interface RegionItem {
  id: string
  name: string
  code: string
  created_at?: string | null
  updated_at?: string | null
}

export interface SchoolItem {
  id: string
  region_id: string
  region_name?: string | null
  name: string
  code: string
  status: string
  created_at?: string | null
  updated_at?: string | null
}

export interface ClassItem {
  id: string
  school_id: string
  school_name?: string | null
  grade: string
  name: string
  academic_year: string
  created_at?: string | null
  updated_at?: string | null
}

export interface SubjectItem {
  id: string
  name: string
  stage: string
  created_at?: string | null
  updated_at?: string | null
}

export interface SystemSettingItem {
  key: string
  value: unknown
  description?: string | null
}

export interface AuditLogItem {
  id: string
  user_id: string
  user_name?: string | null
  action: string
  target_type: string
  target_id: string
  ip?: string | null
  user_agent?: string | null
  detail?: Record<string, unknown>
  created_at: string
}

export interface OrgRegionPackageItem {
  name: string
  code: string
}

export interface OrgSchoolPackageItem {
  region_code: string
  name: string
  code: string
  status: string
}

export interface OrgClassPackageItem {
  school_code: string
  grade: string
  name: string
  academic_year: string
}

export interface OrgSubjectPackageItem {
  name: string
  stage: string
}

export interface OrgDataPackage {
  regions: OrgRegionPackageItem[]
  schools: OrgSchoolPackageItem[]
  classes: OrgClassPackageItem[]
  subjects: OrgSubjectPackageItem[]
}

export interface OrgDataImportSummary {
  dry_run: boolean
  created: Record<'regions' | 'schools' | 'classes' | 'subjects', number>
  skipped: Record<'regions' | 'schools' | 'classes' | 'subjects', number>
  errors: string[]
}

export interface UserClassPackageRef {
  grade: string
  name: string
  academic_year: string
}

export interface UserPackageItem {
  username: string
  name: string
  role: UserRole
  school_code: string
  class: UserClassPackageRef | null
  initial_password?: string
  status?: string
}

export interface UserDataPackage {
  users: UserPackageItem[]
}

export interface UserInitialPasswordItem {
  username: string
  name: string
  role: UserRole
  initial_password: string
}

export interface UserDataImportSummary {
  dry_run: boolean
  created: Record<'users', number>
  skipped: Record<'users', number>
  errors: string[]
  initial_passwords: UserInitialPasswordItem[]
}

export function getAdminUsers(params?: {
  page?: number
  page_size?: number
  keyword?: string
  role?: string
  status?: string
}): Promise<ApiResponse<PaginatedData<AdminUserItem>>> {
  return request.get('/users', { params })
}

export function createAdminUser(data: AdminUserCreate): Promise<ApiResponse<AdminUserItem>> {
  return request.post('/users', data)
}

export function updateAdminUser(id: string, data: AdminUserUpdate): Promise<ApiResponse<AdminUserItem>> {
  return request.patch(`/users/${id}`, data)
}

export function updateAdminUserStatus(id: string, status: string): Promise<ApiResponse<AdminUserItem>> {
  return request.patch(`/users/${id}/status`, { status })
}

export function resetAdminUserPassword(
  id: string,
  newPassword: string
): Promise<ApiResponse<{ updated: boolean; user_id: string }>> {
  return request.post(`/users/${id}/reset-password`, { new_password: newPassword })
}

export function getUserDataTemplate(): Promise<ApiResponse<UserDataPackage>> {
  return request.get('/users/data/template')
}

export function exportUserDataPackage(): Promise<ApiResponse<UserDataPackage>> {
  return request.get('/users/data/export')
}

export function importUserDataPackage(data: {
  dry_run: boolean
  package: UserDataPackage
}): Promise<ApiResponse<UserDataImportSummary>> {
  return request.post('/users/data/import', data)
}

export function getRegions(params?: {
  page?: number
  page_size?: number
  keyword?: string
}): Promise<ApiResponse<PaginatedData<RegionItem>>> {
  return request.get('/org/regions', { params })
}

export function createRegion(data: { name: string; code: string }): Promise<ApiResponse<RegionItem>> {
  return request.post('/org/regions', data)
}

export function updateRegion(id: string, data: Partial<RegionItem>): Promise<ApiResponse<RegionItem>> {
  return request.patch(`/org/regions/${id}`, data)
}

export function deleteRegion(id: string): Promise<ApiResponse<RegionItem>> {
  return request.delete(`/org/regions/${id}`)
}

export function getSchools(params?: {
  page?: number
  page_size?: number
  keyword?: string
  region_id?: string
  status?: string
}): Promise<ApiResponse<PaginatedData<SchoolItem>>> {
  return request.get('/org/schools', { params })
}

export function createSchool(data: {
  region_id: string
  name: string
  code: string
  status: string
}): Promise<ApiResponse<SchoolItem>> {
  return request.post('/org/schools', data)
}

export function updateSchool(id: string, data: Partial<SchoolItem>): Promise<ApiResponse<SchoolItem>> {
  return request.patch(`/org/schools/${id}`, data)
}

export function deleteSchool(id: string): Promise<ApiResponse<SchoolItem>> {
  return request.delete(`/org/schools/${id}`)
}

export function getClasses(params?: {
  page?: number
  page_size?: number
  keyword?: string
  school_id?: string
  grade?: string
}): Promise<ApiResponse<PaginatedData<ClassItem>>> {
  return request.get('/org/classes', { params })
}

export function createClass(data: {
  school_id: string
  grade: string
  name: string
  academic_year: string
}): Promise<ApiResponse<ClassItem>> {
  return request.post('/org/classes', data)
}

export function updateClass(id: string, data: Partial<ClassItem>): Promise<ApiResponse<ClassItem>> {
  return request.patch(`/org/classes/${id}`, data)
}

export function deleteClass(id: string): Promise<ApiResponse<ClassItem>> {
  return request.delete(`/org/classes/${id}`)
}

export function getSubjects(params?: {
  page?: number
  page_size?: number
  keyword?: string
  stage?: string
}): Promise<ApiResponse<PaginatedData<SubjectItem>>> {
  return request.get('/org/subjects', { params })
}

export function createSubject(data: { name: string; stage: string }): Promise<ApiResponse<SubjectItem>> {
  return request.post('/org/subjects', data)
}

export function updateSubject(id: string, data: Partial<SubjectItem>): Promise<ApiResponse<SubjectItem>> {
  return request.patch(`/org/subjects/${id}`, data)
}

export function deleteSubject(id: string): Promise<ApiResponse<SubjectItem>> {
  return request.delete(`/org/subjects/${id}`)
}

export function getOrgDataTemplate(): Promise<ApiResponse<OrgDataPackage>> {
  return request.get('/org/data/template')
}

export function exportOrgDataPackage(): Promise<ApiResponse<OrgDataPackage>> {
  return request.get('/org/data/export')
}

export function importOrgDataPackage(data: {
  dry_run: boolean
  package: OrgDataPackage
}): Promise<ApiResponse<OrgDataImportSummary>> {
  return request.post('/org/data/import', data)
}

export function getSystemSettings(params?: {
  page?: number
  page_size?: number
  keyword?: string
}): Promise<ApiResponse<PaginatedData<SystemSettingItem>>> {
  return request.get('/settings', { params })
}

export function saveSystemSetting(
  key: string,
  data: { value: unknown; description?: string | null }
): Promise<ApiResponse<SystemSettingItem>> {
  return request.put(`/settings/${key}`, data)
}

export function getAuditLogs(params?: {
  page?: number
  page_size?: number
  action?: string
  target_type?: string
  user_id?: string
}): Promise<ApiResponse<PaginatedData<AuditLogItem>>> {
  return request.get('/audit-logs', { params })
}

export function getAdminAICalls(params?: {
  page?: number
  page_size?: number
  scenario?: string
  provider?: string
  status?: string
  review_status?: string
}): Promise<ApiResponse<PaginatedData<AICallItem>>> {
  return request.get('/ai/calls', { params })
}
