import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, UserRole } from '@/types/api'
import { login as loginApi, logout as logoutApi, getCurrentUser, refreshToken as refreshTokenApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>('')
  const refreshTokenVal = ref<string>('')
  const user = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const userRole = computed<UserRole | ''>(() => user.value?.role || '')
  const userName = computed(() => user.value?.name || '')

  function setTokens(accessToken: string, refreshToken: string) {
    token.value = accessToken
    refreshTokenVal.value = refreshToken
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }

  function clearTokens() {
    token.value = ''
    refreshTokenVal.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_info')
  }

  async function login(username: string, password: string) {
    const response = await loginApi({ username, password })
    const { access_token, refresh_token, user: userInfo } = response.data

    setTokens(access_token, refresh_token)
    user.value = userInfo
    localStorage.setItem('user_info', JSON.stringify(userInfo))

    // Redirect to role-based home
    redirectToRoleHome(userInfo.role)
  }

  async function logout() {
    try {
      await logoutApi()
    } catch {
      // Ignore logout API errors
    } finally {
      clearTokens()
      router.push('/login')
    }
  }

  async function refreshAccessToken(): Promise<boolean> {
    try {
      const response = await refreshTokenApi(refreshTokenVal.value)
      const { access_token, refresh_token } = response.data
      setTokens(access_token, refresh_token)
      return true
    } catch {
      clearTokens()
      return false
    }
  }

  async function fetchCurrentUser() {
    try {
      const response = await getCurrentUser()
      user.value = response.data
      localStorage.setItem('user_info', JSON.stringify(response.data))
    } catch {
      clearTokens()
    }
  }

  function initFromStorage() {
    const storedToken = localStorage.getItem('access_token')
    const storedRefreshToken = localStorage.getItem('refresh_token')
    const storedUser = localStorage.getItem('user_info')

    if (storedToken) {
      token.value = storedToken
    }
    if (storedRefreshToken) {
      refreshTokenVal.value = storedRefreshToken
    }
    if (storedUser) {
      try {
        user.value = JSON.parse(storedUser)
      } catch {
        user.value = null
      }
    }
  }

  function redirectToRoleHome(role: UserRole) {
    const roleHomeMap: Record<string, string> = {
      teacher: '/teacher',
      student: '/student',
      researcher: '/research',
      system_admin: '/admin',
      school_admin: '/admin',
      region_admin: '/admin'
    }
    const path = roleHomeMap[role] || '/'
    router.push(path)
  }

  return {
    token,
    refreshTokenVal,
    user,
    isLoggedIn,
    userRole,
    userName,
    login,
    logout,
    refreshAccessToken,
    fetchCurrentUser,
    initFromStorage,
    setTokens,
    clearTokens
  }
})
