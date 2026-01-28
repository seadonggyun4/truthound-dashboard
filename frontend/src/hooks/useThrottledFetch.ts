/**
 * Hook for throttled data fetching on page navigation.
 *
 * Prevents 429 errors by:
 * 1. Throttling fetch calls (minimum interval between calls)
 * 2. Caching results with TTL
 * 3. Skipping fetch if data is still fresh
 */

import { useCallback, useEffect, useRef, useState } from 'react'

interface ThrottledFetchOptions {
  /**
   * Minimum time between fetch calls in milliseconds.
   * @default 500
   */
  throttleMs?: number

  /**
   * Cache TTL in milliseconds. If data was fetched within this time, skip fetch.
   * @default 30000 (30 seconds)
   */
  cacheTtlMs?: number

  /**
   * Whether to fetch on mount.
   * @default true
   */
  fetchOnMount?: boolean
}

interface ThrottledFetchResult<T> {
  data: T | null
  isLoading: boolean
  error: Error | null
  refetch: (force?: boolean) => Promise<void>
  lastFetchedAt: number | null
}

// Global cache for throttled fetches
const fetchCache = new Map<string, { data: unknown; fetchedAt: number }>()
const lastFetchTime = new Map<string, number>()

/**
 * Hook for throttled data fetching with caching.
 *
 * @param key - Unique key for caching and throttling
 * @param fetcher - Async function that fetches data
 * @param options - Throttle and cache options
 *
 * @example
 * const { data, isLoading, refetch } = useThrottledFetch(
 *   'sources-list',
 *   listSources,
 *   { throttleMs: 500, cacheTtlMs: 30000 }
 * )
 */
export function useThrottledFetch<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: ThrottledFetchOptions = {}
): ThrottledFetchResult<T> {
  const {
    throttleMs = 500,
    cacheTtlMs = 30000,
    fetchOnMount = true,
  } = options

  const [data, setData] = useState<T | null>(() => {
    // Initialize from cache if available and fresh
    const cached = fetchCache.get(key)
    if (cached && Date.now() - cached.fetchedAt < cacheTtlMs) {
      return cached.data as T
    }
    return null
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [lastFetchedAt, setLastFetchedAt] = useState<number | null>(() => {
    const cached = fetchCache.get(key)
    return cached?.fetchedAt ?? null
  })

  // Track if component is mounted
  const isMountedRef = useRef(true)

  // Track pending fetch promise for deduplication
  const pendingFetchRef = useRef<Promise<T> | null>(null)

  const doFetch = useCallback(async (force = false): Promise<void> => {
    const now = Date.now()

    // Check throttle (unless forced)
    if (!force) {
      const lastFetch = lastFetchTime.get(key) ?? 0
      if (now - lastFetch < throttleMs) {
        // Throttled - return cached data if available
        const cached = fetchCache.get(key)
        if (cached) {
          setData(cached.data as T)
          setLastFetchedAt(cached.fetchedAt)
        }
        return
      }

      // Check cache TTL (unless forced)
      const cached = fetchCache.get(key)
      if (cached && now - cached.fetchedAt < cacheTtlMs) {
        setData(cached.data as T)
        setLastFetchedAt(cached.fetchedAt)
        return
      }
    }

    // If already fetching, wait for that fetch
    if (pendingFetchRef.current) {
      try {
        const result = await pendingFetchRef.current
        if (isMountedRef.current) {
          setData(result)
          setError(null)
        }
      } catch (e) {
        if (isMountedRef.current) {
          setError(e instanceof Error ? e : new Error(String(e)))
        }
      }
      return
    }

    // Start new fetch
    setIsLoading(true)
    setError(null)
    lastFetchTime.set(key, now)

    const fetchPromise = fetcher()
    pendingFetchRef.current = fetchPromise

    try {
      const result = await fetchPromise

      // Update cache
      fetchCache.set(key, { data: result, fetchedAt: Date.now() })

      if (isMountedRef.current) {
        setData(result)
        setLastFetchedAt(Date.now())
        setError(null)
      }
    } catch (e) {
      if (isMountedRef.current) {
        setError(e instanceof Error ? e : new Error(String(e)))
      }
    } finally {
      pendingFetchRef.current = null
      if (isMountedRef.current) {
        setIsLoading(false)
      }
    }
  }, [key, fetcher, throttleMs, cacheTtlMs])

  // Fetch on mount
  useEffect(() => {
    isMountedRef.current = true

    if (fetchOnMount) {
      doFetch()
    }

    return () => {
      isMountedRef.current = false
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return {
    data,
    isLoading,
    error,
    refetch: doFetch,
    lastFetchedAt,
  }
}

/**
 * Clear cached data for a specific key.
 */
export function clearFetchCache(key: string): void {
  fetchCache.delete(key)
  lastFetchTime.delete(key)
}

/**
 * Clear all cached fetch data.
 */
export function clearAllFetchCache(): void {
  fetchCache.clear()
  lastFetchTime.clear()
}

/**
 * Get cache statistics for debugging.
 */
export function getFetchCacheStats(): { keys: string[]; size: number } {
  return {
    keys: Array.from(fetchCache.keys()),
    size: fetchCache.size,
  }
}
