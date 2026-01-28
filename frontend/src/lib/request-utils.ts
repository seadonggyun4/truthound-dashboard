/**
 * Request utilities for preventing 429 errors.
 *
 * - Request Deduplication: Reuse in-flight requests
 * - Throttle: Limit request frequency
 */

// ============================================
// Request Deduplication
// ============================================

const pendingRequests = new Map<string, Promise<unknown>>()

/**
 * Deduplicate concurrent requests with the same key.
 * If a request with the same key is already in-flight, returns the existing promise.
 *
 * @example
 * // Both calls will share the same API request
 * const [data1, data2] = await Promise.all([
 *   deduplicatedRequest('lineage', () => fetch('/api/lineage')),
 *   deduplicatedRequest('lineage', () => fetch('/api/lineage')),
 * ])
 */
export async function deduplicatedRequest<T>(
  key: string,
  fetcher: () => Promise<T>
): Promise<T> {
  // Return existing request if in-flight
  if (pendingRequests.has(key)) {
    return pendingRequests.get(key) as Promise<T>
  }

  // Create new request and track it
  const promise = fetcher().finally(() => {
    pendingRequests.delete(key)
  })

  pendingRequests.set(key, promise)
  return promise
}

/**
 * Clear a specific pending request (useful for forced refresh).
 */
export function clearPendingRequest(key: string): void {
  pendingRequests.delete(key)
}

/**
 * Clear all pending requests.
 */
export function clearAllPendingRequests(): void {
  pendingRequests.clear()
}

// ============================================
// Throttle
// ============================================

/**
 * Creates a throttled version of a function.
 * The function will be called at most once per `wait` milliseconds.
 *
 * @example
 * const throttledFetch = throttle(fetchData, 1000)
 * throttledFetch() // executes immediately
 * throttledFetch() // ignored (within 1000ms)
 * // after 1000ms...
 * throttledFetch() // executes
 */
export function throttle<T extends (...args: Parameters<T>) => ReturnType<T>>(
  fn: T,
  wait: number
): (...args: Parameters<T>) => ReturnType<T> | undefined {
  let lastCall = 0
  let lastResult: ReturnType<T> | undefined

  return (...args: Parameters<T>): ReturnType<T> | undefined => {
    const now = Date.now()

    if (now - lastCall >= wait) {
      lastCall = now
      lastResult = fn(...args)
      return lastResult
    }

    return lastResult
  }
}

/**
 * Creates a throttled async function that returns the last result if called too frequently.
 * Useful for API calls on navigation.
 *
 * @example
 * const throttledFetch = throttleAsync(fetchLineage, 500)
 * await throttledFetch() // fetches
 * await throttledFetch() // returns cached result (within 500ms)
 */
export function throttleAsync<T extends (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>>>(
  fn: T,
  wait: number
): (...args: Parameters<T>) => Promise<Awaited<ReturnType<T>>> {
  let lastCall = 0
  let lastPromise: Promise<Awaited<ReturnType<T>>> | null = null

  return async (...args: Parameters<T>): Promise<Awaited<ReturnType<T>>> => {
    const now = Date.now()

    if (now - lastCall >= wait || !lastPromise) {
      lastCall = now
      lastPromise = fn(...args)
    }

    return lastPromise
  }
}

// ============================================
// Debounce
// ============================================

/**
 * Creates a debounced version of a function.
 * The function will only be called after `wait` milliseconds of inactivity.
 *
 * @example
 * const debouncedSearch = debounce(search, 300)
 * debouncedSearch('a') // cancelled
 * debouncedSearch('ab') // cancelled
 * debouncedSearch('abc') // executes after 300ms
 */
export function debounce<T extends (...args: Parameters<T>) => void>(
  fn: T,
  wait: number
): ((...args: Parameters<T>) => void) & { cancel: () => void } {
  let timeoutId: ReturnType<typeof setTimeout> | null = null

  const debounced = (...args: Parameters<T>): void => {
    if (timeoutId) {
      clearTimeout(timeoutId)
    }

    timeoutId = setTimeout(() => {
      fn(...args)
      timeoutId = null
    }, wait)
  }

  debounced.cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId)
      timeoutId = null
    }
  }

  return debounced
}

// ============================================
// Request Queue (Rate Limiting)
// ============================================

interface QueuedRequest<T> {
  execute: () => Promise<T>
  resolve: (value: T) => void
  reject: (error: unknown) => void
}

/**
 * A queue that rate-limits requests to prevent 429 errors.
 *
 * @example
 * const queue = new RequestQueue(100) // 100ms between requests
 * await Promise.all([
 *   queue.add(() => fetch('/api/a')),
 *   queue.add(() => fetch('/api/b')),
 *   queue.add(() => fetch('/api/c')),
 * ])
 * // Requests are spaced 100ms apart
 */
export class RequestQueue {
  private queue: QueuedRequest<unknown>[] = []
  private processing = false
  private minInterval: number

  constructor(minInterval = 100) {
    this.minInterval = minInterval
  }

  async add<T>(request: () => Promise<T>): Promise<T> {
    return new Promise<T>((resolve, reject) => {
      this.queue.push({
        execute: request as () => Promise<unknown>,
        resolve: resolve as (value: unknown) => void,
        reject,
      })
      this.process()
    })
  }

  private async process(): Promise<void> {
    if (this.processing || this.queue.length === 0) return

    this.processing = true

    while (this.queue.length > 0) {
      const item = this.queue.shift()!

      try {
        const result = await item.execute()
        item.resolve(result)
      } catch (error) {
        item.reject(error)
      }

      // Wait before next request
      if (this.queue.length > 0) {
        await new Promise((r) => setTimeout(r, this.minInterval))
      }
    }

    this.processing = false
  }

  /**
   * Clear all pending requests in the queue.
   */
  clear(): void {
    const pending = this.queue.splice(0)
    pending.forEach((item) => item.reject(new Error('Queue cleared')))
  }

  /**
   * Get the number of pending requests.
   */
  get pendingCount(): number {
    return this.queue.length
  }
}

// Global request queue instance (100ms between requests)
export const globalRequestQueue = new RequestQueue(100)

// ============================================
// Global Rate Limiter
// ============================================

/**
 * Simple token bucket rate limiter.
 * Allows burst requests up to `bucketSize`, then rate limits.
 */
export class RateLimiter {
  private tokens: number
  private lastRefill: number
  private readonly bucketSize: number
  private readonly refillRate: number // tokens per ms

  /**
   * @param requestsPerSecond - Maximum sustained requests per second
   * @param burstSize - Maximum burst size (default: 2x requestsPerSecond)
   */
  constructor(requestsPerSecond: number, burstSize?: number) {
    this.bucketSize = burstSize ?? requestsPerSecond * 2
    this.refillRate = requestsPerSecond / 1000
    this.tokens = this.bucketSize
    this.lastRefill = Date.now()
  }

  /**
   * Try to acquire a token. Returns true if allowed, false if rate limited.
   */
  tryAcquire(): boolean {
    this.refill()

    if (this.tokens >= 1) {
      this.tokens -= 1
      return true
    }

    return false
  }

  /**
   * Wait until a token is available, then acquire it.
   */
  async acquire(): Promise<void> {
    while (!this.tryAcquire()) {
      // Wait for one token to be available
      const waitTime = Math.ceil(1 / this.refillRate)
      await new Promise((r) => setTimeout(r, waitTime))
    }
  }

  /**
   * Get time in ms until next token is available.
   */
  getWaitTime(): number {
    this.refill()
    if (this.tokens >= 1) return 0
    return Math.ceil((1 - this.tokens) / this.refillRate)
  }

  private refill(): void {
    const now = Date.now()
    const elapsed = now - this.lastRefill
    const tokensToAdd = elapsed * this.refillRate

    this.tokens = Math.min(this.bucketSize, this.tokens + tokensToAdd)
    this.lastRefill = now
  }
}

// Global rate limiter: 8 requests/second (480/min) with burst of 15
// Stays under backend limit of 600 requests/minute with safety margin
export const globalRateLimiter = new RateLimiter(8, 15)
