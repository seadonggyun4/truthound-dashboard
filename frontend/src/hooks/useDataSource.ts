/**
 * React hooks for data source operations
 *
 * Provides convenient hooks for common data source operations
 * with loading states, error handling, and caching.
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import {
  datasourcesApi,
  type SourceListParams,
  type SourceListResponse,
  type ValidationRequest,
  type ValidationResult,
  type ProfileResponse,
  type SchemaResponse,
  type ScanRequest,
  type ScanResult,
  type DriftCompareRequest,
  type DriftResult,
} from '@/api/datasources'
import type {
  DataSource,
  SourceType,
  SourceTypeDefinition,
  CreateSourceRequest,
  UpdateSourceRequest,
  TestConnectionRequest,
  TestConnectionResponse,
  ConnectionTestResult,
} from '@/types/datasources'
import { ApiError } from '@/api/base'

// ============================================================================
// Types
// ============================================================================

export interface UseAsyncState<T> {
  data: T | null
  loading: boolean
  error: ApiError | null
}

export interface UseMutationState<T> {
  data: T | null
  loading: boolean
  error: ApiError | null
  success: boolean
}

// ============================================================================
// Generic Hooks
// ============================================================================

/**
 * Hook for async operations with loading/error state.
 */
function useAsyncOperation<T, TArgs extends unknown[]>(
  operation: (...args: TArgs) => Promise<T>
): [
  (...args: TArgs) => Promise<T | null>,
  UseAsyncState<T> & { reset: () => void }
] {
  const [state, setState] = useState<UseAsyncState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(
    async (...args: TArgs): Promise<T | null> => {
      setState({ data: null, loading: true, error: null })
      try {
        const result = await operation(...args)
        setState({ data: result, loading: false, error: null })
        return result
      } catch (err) {
        const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
        setState({ data: null, loading: false, error })
        return null
      }
    },
    [operation]
  )

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return [execute, { ...state, reset }]
}

// ============================================================================
// Source Types Hooks
// ============================================================================

/**
 * Hook for fetching source type definitions.
 */
export function useSourceTypes() {
  const [state, setState] = useState<{
    types: SourceTypeDefinition[]
    loading: boolean
    error: ApiError | null
  }>({
    types: [],
    loading: false,
    error: null,
  })

  const fetchTypes = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const types = await datasourcesApi.getSourceTypes()
      setState({ types, loading: false, error: null })
      return types
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState((prev) => ({ ...prev, loading: false, error }))
      return null
    }
  }, [])

  useEffect(() => {
    fetchTypes()
  }, [fetchTypes])

  return {
    ...state,
    refetch: fetchTypes,
  }
}

/**
 * Hook for getting a specific source type definition.
 */
export function useSourceTypeDefinition(type: SourceType | null) {
  const [state, setState] = useState<UseAsyncState<SourceTypeDefinition>>({
    data: null,
    loading: false,
    error: null,
  })

  useEffect(() => {
    if (!type) {
      setState({ data: null, loading: false, error: null })
      return
    }

    setState((prev) => ({ ...prev, loading: true, error: null }))
    datasourcesApi
      .getSourceTypeDefinition(type)
      .then((definition) => {
        setState({ data: definition, loading: false, error: null })
      })
      .catch((err) => {
        const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
        setState({ data: null, loading: false, error })
      })
  }, [type])

  return state
}

// ============================================================================
// Sources List Hook
// ============================================================================

/**
 * Hook for listing data sources with pagination and filtering.
 */
export function useSources(initialParams?: SourceListParams) {
  const [params, setParams] = useState<SourceListParams>(initialParams || {})
  const [state, setState] = useState<{
    sources: DataSource[]
    total: number
    loading: boolean
    error: ApiError | null
  }>({
    sources: [],
    total: 0,
    loading: false,
    error: null,
  })

  const fetchSources = useCallback(async (p?: SourceListParams) => {
    const fetchParams = p || params
    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const response = await datasourcesApi.list(fetchParams)
      setState({
        sources: response.items,
        total: response.total,
        loading: false,
        error: null,
      })
      return response
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState((prev) => ({ ...prev, loading: false, error }))
      return null
    }
  }, [params])

  // Initial fetch
  useEffect(() => {
    fetchSources()
  }, [fetchSources])

  const updateParams = useCallback((newParams: Partial<SourceListParams>) => {
    setParams((prev) => ({ ...prev, ...newParams }))
  }, [])

  return {
    ...state,
    params,
    setParams: updateParams,
    refetch: fetchSources,
  }
}

// ============================================================================
// Single Source Hook
// ============================================================================

/**
 * Hook for fetching a single data source.
 */
export function useSource(id: string | null) {
  const [state, setState] = useState<UseAsyncState<DataSource>>({
    data: null,
    loading: false,
    error: null,
  })

  const fetchSource = useCallback(async () => {
    if (!id) {
      setState({ data: null, loading: false, error: null })
      return null
    }

    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const source = await datasourcesApi.get(id)
      setState({ data: source, loading: false, error: null })
      return source
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error })
      return null
    }
  }, [id])

  useEffect(() => {
    fetchSource()
  }, [fetchSource])

  return {
    source: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchSource,
  }
}

// ============================================================================
// CRUD Hooks
// ============================================================================

/**
 * Hook for creating a data source.
 */
export function useCreateSource() {
  const [state, setState] = useState<UseMutationState<DataSource>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const create = useCallback(async (data: CreateSourceRequest) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const source = await datasourcesApi.create(data)
      setState({ data: source, loading: false, error: null, success: true })
      return source
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error, success: false })
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null, success: false })
  }, [])

  return { ...state, create, reset }
}

/**
 * Hook for updating a data source.
 */
export function useUpdateSource() {
  const [state, setState] = useState<UseMutationState<DataSource>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const update = useCallback(async (id: string, data: UpdateSourceRequest) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const source = await datasourcesApi.update(id, data)
      setState({ data: source, loading: false, error: null, success: true })
      return source
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error, success: false })
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null, success: false })
  }, [])

  return { ...state, update, reset }
}

/**
 * Hook for deleting a data source.
 */
export function useDeleteSource() {
  const [state, setState] = useState<UseMutationState<void>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const remove = useCallback(async (id: string) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      await datasourcesApi.delete(id)
      setState({ data: undefined as unknown as null, loading: false, error: null, success: true })
      return true
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error, success: false })
      return false
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null, success: false })
  }, [])

  return { ...state, remove, reset }
}

// ============================================================================
// Connection Testing Hook
// ============================================================================

/**
 * Hook for testing connections.
 */
export function useConnectionTest() {
  const [state, setState] = useState<UseMutationState<TestConnectionResponse>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const test = useCallback(async (request: TestConnectionRequest) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const result = await datasourcesApi.testConnection(request)
      setState({
        data: result,
        loading: false,
        error: null,
        success: result.success,
      })
      return result
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error, success: false })
      return null
    }
  }, [])

  const testExisting = useCallback(async (id: string) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const result = await datasourcesApi.testSourceConnection(id)
      setState({
        data: result as TestConnectionResponse,
        loading: false,
        error: null,
        success: result.success,
      })
      return result
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error, success: false })
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null, success: false })
  }, [])

  return { ...state, test, testExisting, reset }
}

// ============================================================================
// Schema & Profile Hooks
// ============================================================================

/**
 * Hook for schema operations.
 */
export function useSourceSchema(sourceId: string | null) {
  const [state, setState] = useState<UseAsyncState<SchemaResponse>>({
    data: null,
    loading: false,
    error: null,
  })

  const fetchSchema = useCallback(async () => {
    if (!sourceId) return null

    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const schema = await datasourcesApi.getSchema(sourceId)
      setState({ data: schema, loading: false, error: null })
      return schema
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error })
      return null
    }
  }, [sourceId])

  const learnSchema = useCallback(
    async (options?: { infer_constraints?: boolean; sample_size?: number }) => {
      if (!sourceId) return null

      setState((prev) => ({ ...prev, loading: true, error: null }))
      try {
        const schema = await datasourcesApi.learnSchema(sourceId, options)
        setState({ data: schema, loading: false, error: null })
        return schema
      } catch (err) {
        const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
        setState({ data: null, loading: false, error })
        return null
      }
    },
    [sourceId]
  )

  useEffect(() => {
    fetchSchema()
  }, [fetchSchema])

  return {
    schema: state.data,
    loading: state.loading,
    error: state.error,
    refetch: fetchSchema,
    learn: learnSchema,
  }
}

/**
 * Hook for profile operations.
 */
export function useSourceProfile(sourceId: string | null) {
  const [state, setState] = useState<UseAsyncState<ProfileResponse>>({
    data: null,
    loading: false,
    error: null,
  })

  const fetchProfile = useCallback(async () => {
    if (!sourceId) return null

    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const profile = await datasourcesApi.getProfile(sourceId)
      setState({ data: profile, loading: false, error: null })
      return profile
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error })
      return null
    }
  }, [sourceId])

  const runProfile = useCallback(
    async (options?: { sample_size?: number; columns?: string[] }) => {
      if (!sourceId) return null

      setState((prev) => ({ ...prev, loading: true, error: null }))
      try {
        const profile = await datasourcesApi.profile(sourceId, options)
        setState({ data: profile, loading: false, error: null })
        return profile
      } catch (err) {
        const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
        setState({ data: null, loading: false, error })
        return null
      }
    },
    [sourceId]
  )

  return {
    profile: state.data,
    loading: state.loading,
    error: state.error,
    fetch: fetchProfile,
    run: runProfile,
  }
}

// ============================================================================
// Validation Hook
// ============================================================================

/**
 * Hook for running validations.
 */
export function useValidation() {
  const [state, setState] = useState<UseMutationState<ValidationResult>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const validate = useCallback(
    async (sourceId: string, options?: ValidationRequest) => {
      setState({ data: null, loading: true, error: null, success: false })
      try {
        const result = await datasourcesApi.validate(sourceId, options)
        const success = result.status === 'success'
        setState({ data: result, loading: false, error: null, success })
        return result
      } catch (err) {
        const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
        setState({ data: null, loading: false, error, success: false })
        return null
      }
    },
    []
  )

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null, success: false })
  }, [])

  return { ...state, validate, reset }
}

// ============================================================================
// Drift Detection Hook
// ============================================================================

/**
 * Hook for drift detection.
 */
export function useDriftDetection() {
  const [state, setState] = useState<UseMutationState<DriftResult>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const compare = useCallback(async (request: DriftCompareRequest) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const result = await datasourcesApi.compareDrift(request)
      setState({ data: result, loading: false, error: null, success: true })
      return result
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error, success: false })
      return null
    }
  }, [])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null, success: false })
  }, [])

  return { ...state, compare, reset }
}

// ============================================================================
// PII Scanning Hook
// ============================================================================

/**
 * Hook for PII scanning.
 */
export function usePIIScan() {
  const [state, setState] = useState<UseMutationState<ScanResult>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const scan = useCallback(
    async (sourceId: string, options?: ScanRequest) => {
      setState({ data: null, loading: true, error: null, success: false })
      try {
        const result = await datasourcesApi.scan(sourceId, options)
        setState({ data: result, loading: false, error: null, success: true })
        return result
      } catch (err) {
        const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
        setState({ data: null, loading: false, error, success: false })
        return null
      }
    },
    []
  )

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null, success: false })
  }, [])

  return { ...state, scan, reset }
}

// ============================================================================
// Combined Source Operations Hook
// ============================================================================

/**
 * Combined hook for all source operations.
 * Useful for source detail pages.
 */
export function useSourceOperations(sourceId: string | null) {
  const { source, loading: sourceLoading, error: sourceError, refetch } = useSource(sourceId)
  const { schema, loading: schemaLoading, learn: learnSchema } = useSourceSchema(sourceId)
  const { profile, loading: profileLoading, run: runProfile } = useSourceProfile(sourceId)
  const { test, testExisting, loading: testLoading, data: testResult } = useConnectionTest()
  const { validate, loading: validating, data: validationResult } = useValidation()
  const { scan, loading: scanning, data: scanResult } = usePIIScan()

  const testConnection = useCallback(async () => {
    if (!sourceId) return null
    return testExisting(sourceId)
  }, [sourceId, testExisting])

  const runValidation = useCallback(
    async (options?: ValidationRequest) => {
      if (!sourceId) return null
      return validate(sourceId, options)
    },
    [sourceId, validate]
  )

  const runScan = useCallback(
    async (options?: ScanRequest) => {
      if (!sourceId) return null
      return scan(sourceId, options)
    },
    [sourceId, scan]
  )

  return {
    // Source data
    source,
    sourceLoading,
    sourceError,
    refetchSource: refetch,

    // Schema
    schema,
    schemaLoading,
    learnSchema,

    // Profile
    profile,
    profileLoading,
    runProfile,

    // Connection test
    testConnection,
    testLoading,
    testResult,

    // Validation
    runValidation,
    validating,
    validationResult,

    // PII Scan
    runScan,
    scanning,
    scanResult,
  }
}
