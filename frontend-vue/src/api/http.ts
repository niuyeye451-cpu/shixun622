import axios from 'axios'
import type { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import type { ApiResponse } from '@/types'

const api: AxiosInstance = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// ========== Request interceptor: inject JWT ==========
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('access_token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ========== Exponential backoff retry ==========
const MAX_RETRIES = 3
const RETRY_DELAYS = [1000, 2000, 4000]

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as any
    if (!config) return Promise.reject(error)

    config._retryCount = config._retryCount ?? 0

    // 401 → try refresh token once
    if (error.response?.status === 401 && config._retryCount === 0) {
      config._retryCount = 1
      const refreshToken = sessionStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('/api/v1/common/auth/token/refresh', { refresh_token: refreshToken })
          if (res.data?.code === 200 && res.data.data?.access_token) {
            sessionStorage.setItem('access_token', res.data.data.access_token)
            if (config.headers) {
              config.headers.Authorization = `Bearer ${res.data.data.access_token}`
            }
            return api(config)
          }
        } catch {
          // refresh failed → clear and redirect
          sessionStorage.clear()
          window.location.href = '/login'
          return Promise.reject(error)
        }
      }
      sessionStorage.clear()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    // Network/timeout → retry with exponential backoff
    if (!error.response && config._retryCount < MAX_RETRIES) {
      config._retryCount += 1
      const delay = RETRY_DELAYS[config._retryCount - 1] || 4000
      await new Promise((r) => setTimeout(r, delay))
      return api(config)
    }

    return Promise.reject(error)
  },
)

// ========== Unified response unwrapper ==========
async function request<T = any>(method: string, path: string, data?: any): Promise<ApiResponse<T>> {
  const response = await api({ method, url: path, data: method !== 'get' ? data : undefined, params: method === 'get' ? data : undefined })
  return response.data
}

export default api
export { request }
