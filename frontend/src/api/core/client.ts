/**
 * Core API client - base request function and error handling.
 */

const API_BASE = '/api/v1'

export interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>
}

/**
 * Extract error message from API response data.
 */
function extractErrorMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== 'object') return fallback

  const obj = data as Record<string, unknown>

  // Format: { error: { message: "..." } } or { error: "..." }
  if (obj.error) {
    if (typeof obj.error === 'string') return obj.error
    if (typeof obj.error === 'object' && obj.error !== null) {
      const errorObj = obj.error as Record<string, unknown>
      if (typeof errorObj.message === 'string') return errorObj.message
    }
  }

  // Format: { message: "..." }
  if (typeof obj.message === 'string') return obj.message

  // Format: { detail: "..." } (FastAPI default)
  if (typeof obj.detail === 'string') return obj.detail

  return fallback
}

/**
 * API Error with status and response data.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    const fallbackMessage = `API Error: ${status} ${statusText}`
    super(extractErrorMessage(data, fallbackMessage))
    this.name = 'ApiError'
  }
}

/**
 * Make an API request.
 *
 * @param endpoint - API endpoint (e.g., '/sources')
 * @param options - Request options including params
 * @returns Parsed JSON response
 */
export async function request<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, ...init } = options

  // Build URL with query params
  let url = `${API_BASE}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, String(value))
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += `?${queryString}`
    }
  }

  // Set default headers
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(url, {
    ...init,
    headers,
  })

  if (!response.ok) {
    let data
    try {
      data = await response.json()
    } catch {
      // Ignore JSON parse errors
    }
    throw new ApiError(response.status, response.statusText, data)
  }

  // Handle empty responses
  const contentType = response.headers.get('Content-Type')
  if (!contentType || !contentType.includes('application/json')) {
    return {} as T
  }

  return response.json()
}

/**
 * Health check API.
 */
export interface HealthResponse {
  status: string
  version: string
  timestamp: string
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}
