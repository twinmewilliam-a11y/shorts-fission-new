// 统一 API 客户端封装
import { API_BASE_URL } from '../config'

interface ApiResponse<T> {
  data: T | null
  error: string | null
  status: number
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async get<T>(path: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${path}`)
      const status = response.status
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        return { data: null, error: errorData.detail || `HTTP ${status}`, status }
      }
      
      const data = await response.json()
      return { data, error: null, status }
    } catch (e) {
      return { data: null, error: e instanceof Error ? e.message : '网络错误', status: 0 }
    }
  }

  async post<T>(path: string, body?: unknown): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'POST',
        headers: body ? { 'Content-Type': 'application/json' } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      })
      const status = response.status
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        return { data: null, error: errorData.detail || `HTTP ${status}`, status }
      }
      
      const data = await response.json()
      return { data, error: null, status }
    } catch (e) {
      return { data: null, error: e instanceof Error ? e.message : '网络错误', status: 0 }
    }
  }

  async del<T>(path: string): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: 'DELETE',
      })
      const status = response.status
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: '请求失败' }))
        return { data: null, error: errorData.detail || `HTTP ${status}`, status }
      }
      
      const data = await response.json().catch(() => null)
      return { data, error: null, status }
    } catch (e) {
      return { data: null, error: e instanceof Error ? e.message : '网络错误', status: 0 }
    }
  }
}

export const api = new ApiClient(API_BASE_URL)

// 便捷方法
export const fetchJson = async <T>(path: string): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json()
}

export const postJson = async <T>(path: string, body?: unknown): Promise<T> => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  return response.json()
}

export const deleteRequest = async (path: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
}
