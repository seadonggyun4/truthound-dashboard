/**
 * Utility types and functions for the truthound-dashboard type system.
 *
 * This module provides:
 * - Generic utility types for extensibility
 * - Type guards for runtime validation
 * - Factory functions for creating default configurations
 * - Transformation utilities for API responses
 *
 * Design principles:
 * - Protocol-based typing for flexibility
 * - Factory pattern for object creation
 * - Type guards for runtime safety
 * - Transformation functions for API compatibility
 */

// =============================================================================
// Generic Utility Types
// =============================================================================

/**
 * Make specific properties of T optional.
 */
export type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>

/**
 * Make specific properties of T required.
 */
export type RequiredBy<T, K extends keyof T> = Omit<T, K> & Required<Pick<T, K>>

/**
 * Make all properties of T readonly recursively.
 */
export type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends object ? DeepReadonly<T[P]> : T[P]
}

/**
 * Make all properties of T partial recursively.
 */
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P]
}

/**
 * Extract keys of T where values are of type V.
 */
export type KeysOfType<T, V> = {
  [K in keyof T]: T[K] extends V ? K : never
}[keyof T]

/**
 * Union type of all values of T.
 */
export type ValueOf<T> = T[keyof T]

/**
 * Extract the element type from an array type.
 */
export type ArrayElement<T> = T extends readonly (infer U)[] ? U : never

/**
 * Branded type for type-safe identifiers.
 */
export type Brand<T, B extends string> = T & { __brand: B }

/**
 * Type-safe ID types using branding.
 */
export type SourceId = Brand<string, 'SourceId'>
export type CheckpointId = Brand<string, 'CheckpointId'>
export type ValidationId = Brand<string, 'ValidationId'>
export type ReportId = Brand<string, 'ReportId'>
export type UserId = Brand<string, 'UserId'>

// =============================================================================
// Result Types (for error handling)
// =============================================================================

/**
 * Success result type.
 */
export interface Success<T> {
  success: true
  data: T
  error?: never
}

/**
 * Failure result type.
 */
export interface Failure<E = Error> {
  success: false
  data?: never
  error: E
}

/**
 * Result type for operations that can fail.
 */
export type Result<T, E = Error> = Success<T> | Failure<E>

/**
 * Create a success result.
 */
export function success<T>(data: T): Success<T> {
  return { success: true, data }
}

/**
 * Create a failure result.
 */
export function failure<E = Error>(error: E): Failure<E> {
  return { success: false, error }
}

/**
 * Check if result is success.
 */
export function isSuccess<T, E>(result: Result<T, E>): result is Success<T> {
  return result.success === true
}

/**
 * Check if result is failure.
 */
export function isFailure<T, E>(result: Result<T, E>): result is Failure<E> {
  return result.success === false
}

/**
 * Unwrap a result, throwing if it's a failure.
 */
export function unwrap<T, E>(result: Result<T, E>): T {
  if (isSuccess(result)) {
    return result.data
  }
  throw result.error
}

/**
 * Unwrap a result with a default value.
 */
export function unwrapOr<T, E>(result: Result<T, E>, defaultValue: T): T {
  if (isSuccess(result)) {
    return result.data
  }
  return defaultValue
}

// =============================================================================
// Async Result Types
// =============================================================================

/**
 * Async result type for API operations.
 */
export type AsyncResult<T, E = Error> = Promise<Result<T, E>>

/**
 * Wrap an async operation in a Result.
 */
export async function tryCatch<T, E = Error>(
  fn: () => Promise<T>,
  errorHandler?: (error: unknown) => E
): AsyncResult<T, E> {
  try {
    const data = await fn()
    return success(data)
  } catch (error) {
    const processedError = errorHandler
      ? errorHandler(error)
      : (error as E)
    return failure(processedError)
  }
}

// =============================================================================
// Pagination Types
// =============================================================================

/**
 * Pagination parameters.
 */
export interface PaginationParams {
  page?: number
  pageSize?: number
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

/**
 * Paginated response structure.
 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

/**
 * Create a paginated response from items and params.
 */
export function createPaginatedResponse<T>(
  items: T[],
  total: number,
  params: PaginationParams
): PaginatedResponse<T> {
  const page = params.page || 1
  const pageSize = params.pageSize || 20
  const totalPages = Math.ceil(total / pageSize)

  return {
    items,
    total,
    page,
    pageSize,
    totalPages,
    hasNext: page < totalPages,
    hasPrev: page > 1,
  }
}

// =============================================================================
// Status Types
// =============================================================================

/**
 * Generic status type for entities.
 */
export type EntityStatus = 'active' | 'inactive' | 'pending' | 'archived' | 'deleted'

/**
 * Operation status type.
 */
export type OperationStatus = 'idle' | 'loading' | 'success' | 'error'

/**
 * Severity levels (standardized across the system).
 */
export type Severity = 'critical' | 'error' | 'warning' | 'info'

/**
 * Severity order for sorting.
 */
export const SEVERITY_ORDER: Record<Severity, number> = {
  critical: 0,
  error: 1,
  warning: 2,
  info: 3,
}

/**
 * Compare severities for sorting.
 */
export function compareSeverity(a: Severity, b: Severity): number {
  return SEVERITY_ORDER[a] - SEVERITY_ORDER[b]
}

/**
 * Check if severity is at or above a threshold.
 */
export function isSeverityAtOrAbove(severity: Severity, threshold: Severity): boolean {
  return SEVERITY_ORDER[severity] <= SEVERITY_ORDER[threshold]
}

// =============================================================================
// Type Guards
// =============================================================================

/**
 * Check if value is non-null and non-undefined.
 */
export function isDefined<T>(value: T | null | undefined): value is T {
  return value !== null && value !== undefined
}

/**
 * Check if value is a string.
 */
export function isString(value: unknown): value is string {
  return typeof value === 'string'
}

/**
 * Check if value is a number.
 */
export function isNumber(value: unknown): value is number {
  return typeof value === 'number' && !isNaN(value)
}

/**
 * Check if value is a boolean.
 */
export function isBoolean(value: unknown): value is boolean {
  return typeof value === 'boolean'
}

/**
 * Check if value is an array.
 */
export function isArray<T = unknown>(value: unknown): value is T[] {
  return Array.isArray(value)
}

/**
 * Check if value is a plain object.
 */
export function isPlainObject(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === 'object' &&
    value !== null &&
    !Array.isArray(value) &&
    Object.prototype.toString.call(value) === '[object Object]'
  )
}

/**
 * Check if value is a function.
 */
export function isFunction(value: unknown): value is (...args: unknown[]) => unknown {
  return typeof value === 'function'
}

/**
 * Check if value is a valid date.
 */
export function isValidDate(value: unknown): value is Date {
  return value instanceof Date && !isNaN(value.getTime())
}

/**
 * Check if value is a valid ISO date string.
 */
export function isISODateString(value: unknown): value is string {
  if (!isString(value)) return false
  const date = new Date(value)
  return isValidDate(date) && value === date.toISOString()
}

// =============================================================================
// Transformation Utilities
// =============================================================================

/**
 * Convert snake_case keys to camelCase.
 */
export function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

/**
 * Convert camelCase keys to snake_case.
 */
export function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
}

/**
 * Transform object keys from snake_case to camelCase.
 */
export function transformKeysToCamel<T extends Record<string, unknown>>(
  obj: T
): Record<string, unknown> {
  if (!isPlainObject(obj)) return obj as Record<string, unknown>

  const result: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = snakeToCamel(key)
    if (isPlainObject(value)) {
      result[camelKey] = transformKeysToCamel(value as Record<string, unknown>)
    } else if (isArray(value)) {
      result[camelKey] = value.map((item) =>
        isPlainObject(item) ? transformKeysToCamel(item as Record<string, unknown>) : item
      )
    } else {
      result[camelKey] = value
    }
  }
  return result
}

/**
 * Transform object keys from camelCase to snake_case.
 */
export function transformKeysToSnake<T extends Record<string, unknown>>(
  obj: T
): Record<string, unknown> {
  if (!isPlainObject(obj)) return obj as Record<string, unknown>

  const result: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = camelToSnake(key)
    if (isPlainObject(value)) {
      result[snakeKey] = transformKeysToSnake(value as Record<string, unknown>)
    } else if (isArray(value)) {
      result[snakeKey] = value.map((item) =>
        isPlainObject(item) ? transformKeysToSnake(item as Record<string, unknown>) : item
      )
    } else {
      result[snakeKey] = value
    }
  }
  return result
}

// =============================================================================
// Validation Utilities
// =============================================================================

/**
 * Validation error type.
 */
export interface ValidationError {
  field: string
  message: string
  code?: string
}

/**
 * Validation result type.
 */
export interface ValidationResult {
  valid: boolean
  errors: ValidationError[]
}

/**
 * Create a validation error.
 */
export function createValidationError(
  field: string,
  message: string,
  code?: string
): ValidationError {
  return { field, message, code }
}

/**
 * Create a successful validation result.
 */
export function validResult(): ValidationResult {
  return { valid: true, errors: [] }
}

/**
 * Create a failed validation result.
 */
export function invalidResult(errors: ValidationError[]): ValidationResult {
  return { valid: false, errors }
}

/**
 * Combine multiple validation results.
 */
export function combineValidationResults(...results: ValidationResult[]): ValidationResult {
  const allErrors = results.flatMap((r) => r.errors)
  return allErrors.length === 0
    ? validResult()
    : invalidResult(allErrors)
}

// =============================================================================
// Factory Utilities
// =============================================================================

/**
 * Factory function type.
 */
export type Factory<T, C = void> = C extends void ? () => T : (config: C) => T

/**
 * Registry for factory functions.
 */
export class FactoryRegistry<T, K extends string = string> {
  private factories: Map<K, Factory<T, unknown>> = new Map()

  /**
   * Register a factory function.
   */
  register<C>(key: K, factory: Factory<T, C>): void {
    this.factories.set(key, factory as Factory<T, unknown>)
  }

  /**
   * Get a factory function.
   */
  get<C>(key: K): Factory<T, C> | undefined {
    return this.factories.get(key) as Factory<T, C> | undefined
  }

  /**
   * Create an instance using a registered factory.
   */
  create<C>(key: K, config?: C): T {
    const factory = this.get<C>(key)
    if (!factory) {
      throw new Error(`No factory registered for key: ${key}`)
    }
    return config !== undefined ? (factory as (config: C) => T)(config) : (factory as () => T)()
  }

  /**
   * Check if a factory is registered.
   */
  has(key: K): boolean {
    return this.factories.has(key)
  }

  /**
   * Get all registered keys.
   */
  keys(): K[] {
    return Array.from(this.factories.keys())
  }
}

// =============================================================================
// Memoization Utilities
// =============================================================================

/**
 * Simple memoization for functions with a single argument.
 */
export function memoize<T, R>(fn: (arg: T) => R): (arg: T) => R {
  const cache = new Map<T, R>()
  return (arg: T): R => {
    if (cache.has(arg)) {
      return cache.get(arg)!
    }
    const result = fn(arg)
    cache.set(arg, result)
    return result
  }
}

/**
 * Memoize with a custom cache key function.
 */
export function memoizeWithKey<T extends unknown[], R>(
  fn: (...args: T) => R,
  keyFn: (...args: T) => string
): (...args: T) => R {
  const cache = new Map<string, R>()
  return (...args: T): R => {
    const key = keyFn(...args)
    if (cache.has(key)) {
      return cache.get(key)!
    }
    const result = fn(...args)
    cache.set(key, result)
    return result
  }
}

// =============================================================================
// Date Utilities
// =============================================================================

/**
 * Format a date as ISO string.
 */
export function toISOString(date: Date | string | number): string {
  return new Date(date).toISOString()
}

/**
 * Parse an ISO date string.
 */
export function fromISOString(isoString: string): Date {
  return new Date(isoString)
}

/**
 * Format duration in milliseconds to human-readable string.
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
  return `${Math.floor(ms / 3600000)}h ${Math.floor((ms % 3600000) / 60000)}m`
}

/**
 * Get relative time string (e.g., "2 hours ago").
 */
export function relativeTime(date: Date | string | number): string {
  const now = Date.now()
  const then = new Date(date).getTime()
  const diff = now - then

  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`
  if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`
  if (minutes > 0) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`
  return 'just now'
}

// =============================================================================
// String Utilities
// =============================================================================

/**
 * Truncate a string to a maximum length.
 */
export function truncate(str: string, maxLength: number, suffix = '...'): string {
  if (str.length <= maxLength) return str
  return str.slice(0, maxLength - suffix.length) + suffix
}

/**
 * Capitalize the first letter of a string.
 */
export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1)
}

/**
 * Convert string to title case.
 */
export function titleCase(str: string): string {
  return str
    .toLowerCase()
    .split(' ')
    .map((word) => capitalize(word))
    .join(' ')
}

/**
 * Format bytes to human-readable string.
 */
export function formatBytes(bytes: number, decimals = 2): string {
  if (bytes === 0) return '0 Bytes'

  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(decimals))} ${sizes[i]}`
}

// =============================================================================
// Object Utilities
// =============================================================================

/**
 * Deep clone an object.
 */
export function deepClone<T>(obj: T): T {
  if (obj === null || typeof obj !== 'object') return obj
  if (obj instanceof Date) return new Date(obj.getTime()) as unknown as T
  if (obj instanceof Array) return obj.map((item) => deepClone(item)) as unknown as T
  if (obj instanceof Object) {
    const copy = {} as T
    for (const key in obj) {
      if (Object.prototype.hasOwnProperty.call(obj, key)) {
        (copy as Record<string, unknown>)[key] = deepClone((obj as Record<string, unknown>)[key])
      }
    }
    return copy
  }
  return obj
}

/**
 * Merge objects deeply.
 */
export function deepMerge<T extends Record<string, unknown>>(
  target: T,
  ...sources: Partial<T>[]
): T {
  const result = deepClone(target)

  for (const source of sources) {
    if (!source) continue

    for (const key in source) {
      if (Object.prototype.hasOwnProperty.call(source, key)) {
        const targetValue = result[key]
        const sourceValue = source[key]

        if (isPlainObject(targetValue) && isPlainObject(sourceValue)) {
          (result as Record<string, unknown>)[key] = deepMerge(
            targetValue as Record<string, unknown>,
            sourceValue as Record<string, unknown>
          )
        } else {
          (result as Record<string, unknown>)[key] = deepClone(sourceValue)
        }
      }
    }
  }

  return result
}

/**
 * Pick specific keys from an object.
 */
export function pick<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Pick<T, K> {
  const result = {} as Pick<T, K>
  for (const key of keys) {
    if (key in obj) {
      result[key] = obj[key]
    }
  }
  return result
}

/**
 * Omit specific keys from an object.
 */
export function omit<T extends Record<string, unknown>, K extends keyof T>(
  obj: T,
  keys: K[]
): Omit<T, K> {
  const result = { ...obj }
  for (const key of keys) {
    delete result[key]
  }
  return result as Omit<T, K>
}

/**
 * Filter object entries by a predicate.
 */
export function filterObject<T extends Record<string, unknown>>(
  obj: T,
  predicate: (key: string, value: unknown) => boolean
): Partial<T> {
  const result: Partial<T> = {}
  for (const [key, value] of Object.entries(obj)) {
    if (predicate(key, value)) {
      (result as Record<string, unknown>)[key] = value
    }
  }
  return result
}
