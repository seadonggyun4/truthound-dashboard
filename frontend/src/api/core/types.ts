/**
 * Common types used across API modules.
 */

/**
 * Paginated list response.
 */
export interface PaginatedResponse<T> {
  data: T[]
  total: number
  offset: number
  limit: number
}

/**
 * Simple message response.
 */
export interface MessageResponse {
  message: string
}

/**
 * OK response for delete operations.
 */
export interface OkResponse {
  ok: boolean
}
