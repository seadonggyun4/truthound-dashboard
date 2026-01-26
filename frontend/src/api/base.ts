/**
 * Base API client with typed request/response handling
 *
 * Provides a consistent interface for all API modules with:
 * - Automatic retry with exponential backoff
 * - Request/response interceptors
 * - Request deduplication
 * - Timeout handling
 * - Error transformation
 *
 * Design principles:
 * - Protocol-based extensibility
 * - Composable middleware pattern
 * - Type-safe request/response handling
 */

const API_BASE = '/api/v1'

// ============================================================================
// Configuration
// ============================================================================

export interface ApiClientConfig {
  /** Base URL for API requests */
  baseUrl: string
  /** Default request timeout in milliseconds */
  timeout: number
  /** Maximum retry attempts for failed requests */
  maxRetries: number
  /** Base delay for exponential backoff (ms) */
  retryDelay: number
  /** HTTP status codes that trigger a retry */
  retryStatusCodes: number[]
  /** Enable request deduplication */
  deduplication: boolean
}

const DEFAULT_CONFIG: ApiClientConfig = {
  baseUrl: API_BASE,
  timeout: 30000,
  maxRetries: 3,
  retryDelay: 1000,
  retryStatusCodes: [408, 429, 500, 502, 503, 504],
  deduplication: true,
}

let config: ApiClientConfig = { ...DEFAULT_CONFIG }

/**
 * Configure the API client.
 */
export function configureApiClient(newConfig: Partial<ApiClientConfig>): void {
  config = { ...config, ...newConfig }
}

/**
 * Get the current API client configuration.
 */
export function getApiClientConfig(): ApiClientConfig {
  return { ...config }
}

// ============================================================================
// Error Types
// ============================================================================

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown,
    public retryable: boolean = false
  ) {
    super(`API Error: ${status} ${statusText}`)
    this.name = 'ApiError'
  }

  /**
   * Check if error is a specific status code.
   */
  is(status: number): boolean {
    return this.status === status
  }

  /**
   * Check if error is a client error (4xx).
   */
  isClientError(): boolean {
    return this.status >= 400 && this.status < 500
  }

  /**
   * Check if error is a server error (5xx).
   */
  isServerError(): boolean {
    return this.status >= 500
  }

  /**
   * Check if error is a network error.
   */
  isNetworkError(): boolean {
    return this.status === 0
  }

  /**
   * Check if error is a timeout.
   */
  isTimeout(): boolean {
    return this.status === 408
  }

  /**
   * Check if error is rate limited.
   */
  isRateLimited(): boolean {
    return this.status === 429
  }

  /**
   * Check if error is not found.
   */
  isNotFound(): boolean {
    return this.status === 404
  }

  /**
   * Check if error is unauthorized.
   */
  isUnauthorized(): boolean {
    return this.status === 401
  }

  /**
   * Check if error is forbidden.
   */
  isForbidden(): boolean {
    return this.status === 403
  }

  /**
   * Get error message from response data.
   */
  getMessage(): string {
    if (this.data && typeof this.data === 'object') {
      const data = this.data as Record<string, unknown>
      if (typeof data.detail === 'string') {
        return data.detail
      }
      if (typeof data.message === 'string') {
        return data.message
      }
      if (typeof data.error === 'string') {
        return data.error
      }
      // Handle validation errors array
      if (Array.isArray(data.detail)) {
        return data.detail
          .map((err: { msg?: string; message?: string }) => err.msg || err.message)
          .filter(Boolean)
          .join(', ')
      }
    }
    return this.statusText
  }

  /**
   * Get validation errors if present.
   */
  getValidationErrors(): Array<{ field: string; message: string }> {
    if (this.data && typeof this.data === 'object') {
      const data = this.data as Record<string, unknown>
      if (Array.isArray(data.detail)) {
        return data.detail.map((err: { loc?: string[]; msg?: string }) => ({
          field: err.loc ? err.loc.join('.') : 'unknown',
          message: err.msg || 'Validation error',
        }))
      }
    }
    return []
  }

  /**
   * Convert to a plain object for serialization.
   */
  toJSON(): Record<string, unknown> {
    return {
      status: this.status,
      statusText: this.statusText,
      message: this.getMessage(),
      data: this.data,
      retryable: this.retryable,
    }
  }
}

// ============================================================================
// Interceptor Types
// ============================================================================

/**
 * Request interceptor function type.
 */
export type RequestInterceptor = (
  endpoint: string,
  init: RequestInit
) => Promise<{ endpoint: string; init: RequestInit }> | { endpoint: string; init: RequestInit }

/**
 * Response interceptor function type.
 */
export type ResponseInterceptor = (
  response: Response,
  endpoint: string
) => Promise<Response> | Response

/**
 * Error interceptor function type.
 */
export type ErrorInterceptor = (
  error: ApiError,
  endpoint: string
) => Promise<ApiError | null> | ApiError | null

// Interceptor registries
const requestInterceptors: RequestInterceptor[] = []
const responseInterceptors: ResponseInterceptor[] = []
const errorInterceptors: ErrorInterceptor[] = []

/**
 * Add a request interceptor.
 */
export function addRequestInterceptor(interceptor: RequestInterceptor): () => void {
  requestInterceptors.push(interceptor)
  return () => {
    const index = requestInterceptors.indexOf(interceptor)
    if (index !== -1) requestInterceptors.splice(index, 1)
  }
}

/**
 * Add a response interceptor.
 */
export function addResponseInterceptor(interceptor: ResponseInterceptor): () => void {
  responseInterceptors.push(interceptor)
  return () => {
    const index = responseInterceptors.indexOf(interceptor)
    if (index !== -1) responseInterceptors.splice(index, 1)
  }
}

/**
 * Add an error interceptor.
 */
export function addErrorInterceptor(interceptor: ErrorInterceptor): () => void {
  errorInterceptors.push(interceptor)
  return () => {
    const index = errorInterceptors.indexOf(interceptor)
    if (index !== -1) errorInterceptors.splice(index, 1)
  }
}

/**
 * Clear all interceptors.
 */
export function clearInterceptors(): void {
  requestInterceptors.length = 0
  responseInterceptors.length = 0
  errorInterceptors.length = 0
}

// ============================================================================
// Request Types
// ============================================================================

export interface RequestOptions {
  /** Query parameters */
  params?: Record<string, string | number | boolean | string[] | undefined | null>
  /** Request headers */
  headers?: HeadersInit
  /** Request timeout in milliseconds */
  timeout?: number
  /** AbortSignal for cancellation */
  signal?: AbortSignal
  /** Override max retries for this request */
  maxRetries?: number
  /** Skip retry logic */
  skipRetry?: boolean
  /** Skip request deduplication */
  skipDeduplication?: boolean
  /** Custom cache key for deduplication */
  cacheKey?: string
  /** Response type hint */
  responseType?: 'json' | 'blob' | 'text' | 'arrayBuffer'
}

// ============================================================================
// Request Deduplication
// ============================================================================

interface PendingRequest {
  promise: Promise<unknown>
  abortController: AbortController
  refCount: number
}

const pendingRequests = new Map<string, PendingRequest>()

/**
 * Generate a cache key for request deduplication.
 */
function generateCacheKey(method: string, endpoint: string, body?: unknown): string {
  const bodyHash = body ? JSON.stringify(body) : ''
  return `${method}:${endpoint}:${bodyHash}`
}

/**
 * Clear all pending requests.
 */
export function clearPendingRequests(): void {
  pendingRequests.forEach((req) => req.abortController.abort())
  pendingRequests.clear()
}

// ============================================================================
// Retry Logic
// ============================================================================

/**
 * Calculate delay for exponential backoff with jitter.
 */
function calculateBackoffDelay(attempt: number, baseDelay: number): number {
  const exponentialDelay = baseDelay * Math.pow(2, attempt)
  const jitter = Math.random() * 0.3 * exponentialDelay
  return Math.min(exponentialDelay + jitter, 30000) // Cap at 30 seconds
}

/**
 * Check if a status code should trigger a retry.
 */
function shouldRetry(status: number, options: RequestOptions): boolean {
  if (options.skipRetry) return false
  return config.retryStatusCodes.includes(status)
}

/**
 * Sleep for a specified duration.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// ============================================================================
// API Client Core
// ============================================================================

/**
 * Build URL with query parameters.
 */
function buildUrl(
  endpoint: string,
  params?: Record<string, string | number | boolean | string[] | undefined | null>
): string {
  let url = `${config.baseUrl}${endpoint}`

  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          // Handle array parameters
          value.forEach((v) => searchParams.append(key, String(v)))
        } else {
          searchParams.append(key, String(value))
        }
      }
    })
    const queryString = searchParams.toString()
    if (queryString) {
      url += `?${queryString}`
    }
  }

  return url
}

/**
 * Execute a single request attempt.
 */
async function executeRequest<T>(
  method: string,
  url: string,
  init: RequestInit,
  options: RequestOptions
): Promise<T> {
  const response = await fetch(url, init)

  // Run response interceptors
  let processedResponse = response
  for (const interceptor of responseInterceptors) {
    processedResponse = await interceptor(processedResponse, url)
  }

  if (!processedResponse.ok) {
    let data: unknown
    try {
      data = await processedResponse.json()
    } catch {
      // Ignore JSON parse errors
    }
    const retryable = shouldRetry(processedResponse.status, options)
    throw new ApiError(processedResponse.status, processedResponse.statusText, data, retryable)
  }

  // Handle response based on type
  const contentType = processedResponse.headers.get('Content-Type')
  const responseType = options.responseType || 'json'

  if (responseType === 'blob') {
    return processedResponse.blob() as Promise<T>
  }

  if (responseType === 'text') {
    return processedResponse.text() as Promise<T>
  }

  if (responseType === 'arrayBuffer') {
    return processedResponse.arrayBuffer() as Promise<T>
  }

  // Default JSON handling
  if (!contentType || !contentType.includes('application/json')) {
    return {} as T
  }

  return processedResponse.json()
}

/**
 * Make an API request with retry support.
 */
async function request<T>(
  method: string,
  endpoint: string,
  body?: unknown,
  options: RequestOptions = {}
): Promise<T> {
  const {
    params,
    headers: customHeaders,
    timeout = config.timeout,
    signal,
    maxRetries = config.maxRetries,
    skipDeduplication = false,
    cacheKey: customCacheKey,
  } = options

  const url = buildUrl(endpoint, params)

  // Request deduplication for GET requests
  const isReadOnly = method === 'GET' || method === 'HEAD'
  const cacheKey = customCacheKey || generateCacheKey(method, endpoint, body)

  if (config.deduplication && isReadOnly && !skipDeduplication) {
    const pending = pendingRequests.get(cacheKey)
    if (pending) {
      pending.refCount++
      try {
        return (await pending.promise) as T
      } finally {
        pending.refCount--
        if (pending.refCount === 0) {
          pendingRequests.delete(cacheKey)
        }
      }
    }
  }

  // Setup headers
  const headers = new Headers(customHeaders)
  if (body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  // Setup abort controller for timeout
  const controller = new AbortController()
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  const fetchSignal = signal
    ? anySignal([signal, controller.signal])
    : controller.signal

  // Build request init
  let init: RequestInit = {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    signal: fetchSignal,
  }

  // Run request interceptors
  let processedEndpoint = url
  for (const interceptor of requestInterceptors) {
    const result = await interceptor(processedEndpoint, init)
    processedEndpoint = result.endpoint
    init = result.init
  }

  // Execute with retry logic
  const executeWithRetry = async (): Promise<T> => {
    let lastError: ApiError | null = null
    const attempts = options.skipRetry ? 1 : maxRetries + 1

    for (let attempt = 0; attempt < attempts; attempt++) {
      try {
        // Set timeout
        timeoutId = setTimeout(() => controller.abort(), timeout)

        const result = await executeRequest<T>(method, processedEndpoint, init, options)

        if (timeoutId) clearTimeout(timeoutId)
        return result
      } catch (error) {
        if (timeoutId) clearTimeout(timeoutId)

        // Handle non-ApiError
        if (!(error instanceof ApiError)) {
          if (error instanceof Error && error.name === 'AbortError') {
            lastError = new ApiError(408, 'Request Timeout', { detail: 'Request timed out' }, true)
          } else if (error instanceof Error) {
            lastError = new ApiError(0, 'Network Error', { detail: error.message }, true)
          } else {
            throw error
          }
        } else {
          lastError = error
        }

        // Run error interceptors
        for (const interceptor of errorInterceptors) {
          const result = await interceptor(lastError, processedEndpoint)
          if (result === null) {
            // Interceptor handled the error, return empty result
            return {} as T
          }
          lastError = result
        }

        // Check if we should retry
        const shouldAttemptRetry = lastError.retryable && attempt < attempts - 1

        if (shouldAttemptRetry) {
          const delay = calculateBackoffDelay(attempt, config.retryDelay)
          await sleep(delay)
          continue
        }

        throw lastError
      }
    }

    throw lastError || new ApiError(0, 'Unknown Error', { detail: 'Request failed' })
  }

  // Create promise for deduplication
  const requestPromise = executeWithRetry()

  if (config.deduplication && isReadOnly && !skipDeduplication) {
    pendingRequests.set(cacheKey, {
      promise: requestPromise,
      abortController: controller,
      refCount: 1,
    })

    try {
      const result = await requestPromise
      return result
    } finally {
      const pending = pendingRequests.get(cacheKey)
      if (pending) {
        pending.refCount--
        if (pending.refCount === 0) {
          pendingRequests.delete(cacheKey)
        }
      }
    }
  }

  return requestPromise
}

/**
 * Combine multiple AbortSignals into one.
 */
function anySignal(signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController()

  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort(signal.reason)
      return controller.signal
    }
    signal.addEventListener('abort', () => controller.abort(signal.reason), {
      once: true,
    })
  }

  return controller.signal
}

// ============================================================================
// Public API Client
// ============================================================================

/**
 * Typed API client for making HTTP requests.
 */
export const apiClient = {
  /**
   * Make a GET request.
   */
  get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>('GET', endpoint, undefined, options)
  },

  /**
   * Make a POST request.
   */
  post<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('POST', endpoint, body, options)
  },

  /**
   * Make a PUT request.
   */
  put<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('PUT', endpoint, body, options)
  },

  /**
   * Make a PATCH request.
   */
  patch<T>(endpoint: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>('PATCH', endpoint, body, options)
  },

  /**
   * Make a DELETE request.
   */
  delete<T = void>(endpoint: string, options?: RequestOptions): Promise<T> {
    return request<T>('DELETE', endpoint, undefined, options)
  },

  /**
   * Download a file as a blob.
   */
  download(endpoint: string, options?: RequestOptions): Promise<Blob> {
    return request<Blob>('GET', endpoint, undefined, {
      ...options,
      responseType: 'blob',
    })
  },

  /**
   * Upload a file.
   */
  async upload<T>(
    endpoint: string,
    file: File | Blob,
    fieldName = 'file',
    additionalData?: Record<string, string>,
    options?: Omit<RequestOptions, 'headers'>
  ): Promise<T> {
    const formData = new FormData()
    formData.append(fieldName, file)

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value)
      })
    }

    // For FormData, let the browser set the Content-Type with boundary
    const response = await fetch(buildUrl(endpoint, options?.params), {
      method: 'POST',
      body: formData,
      signal: options?.signal,
    })

    if (!response.ok) {
      let data: unknown
      try {
        data = await response.json()
      } catch {
        // Ignore JSON parse errors
      }
      throw new ApiError(response.status, response.statusText, data)
    }

    return response.json()
  },
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Create an AbortController with timeout.
 */
export function createTimeoutController(timeoutMs: number): {
  controller: AbortController
  cleanup: () => void
} {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  return {
    controller,
    cleanup: () => clearTimeout(timeoutId),
  }
}

/**
 * Check if an error is an ApiError.
 */
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}

/**
 * Get a user-friendly error message from any error.
 */
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.getMessage()
  }
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return 'An unexpected error occurred'
}

/**
 * Retry a function with exponential backoff.
 */
export async function withRetry<T>(
  fn: () => Promise<T>,
  options: {
    maxRetries?: number
    retryDelay?: number
    shouldRetry?: (error: unknown) => boolean
  } = {}
): Promise<T> {
  const {
    maxRetries = config.maxRetries,
    retryDelay = config.retryDelay,
    shouldRetry = () => true,
  } = options

  let lastError: unknown

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error

      if (attempt < maxRetries && shouldRetry(error)) {
        const delay = calculateBackoffDelay(attempt, retryDelay)
        await sleep(delay)
        continue
      }

      throw error
    }
  }

  throw lastError
}

export default apiClient
