import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/api'

const request: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // Handle 401 - try token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token')

      if (refreshToken && !isRefreshing) {
        originalRequest._retry = true
        isRefreshing = true

        try {
          const response = await axios.post<ApiResponse>('/api/v1/auth/refresh', {
            refresh_token: refreshToken
          })

          const newAccessToken = response.data.data.access_token
          const newRefreshToken = response.data.data.refresh_token

          localStorage.setItem('access_token', newAccessToken)
          localStorage.setItem('refresh_token', newRefreshToken)

          onTokenRefreshed(newAccessToken)
          isRefreshing = false

          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return request(originalRequest)
        } catch (refreshError) {
          isRefreshing = false
          refreshSubscribers = []
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user_info')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }

      // Queue requests while refreshing
      if (isRefreshing) {
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(request(originalRequest))
          })
        })
      }

      // No refresh token, redirect to login
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user_info')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // Handle other errors
    const message = error.response?.data?.message || error.message || '请求失败'
    ElMessage.error(message)

    return Promise.reject(error)
  }
)

// Unwrap response data
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>): any => {
    return response.data
  }
)

export default request
