/**
 * React hooks for data source operations
 *
 * Provides convenient hooks for common data source operations
 * with loading states, error handling, and caching.
 */

import { useState, useCallback, useEffect } from 'react'
import {
  listSources,
  getSource,
  createSource,
  updateSource,
  deleteSource,
  testSourceConnection,
  testConnectionConfig,
  getSupportedSourceTypes,
  type Source,
  type SourceType,
  type SourceTypeDefinition,
  type TestConnectionResult,
} from '@/api/modules/sources'
import {
  getSourceSchema,
  learnSchema,
  type Schema,
} from '@/api/modules/schemas'
import {
  profileSource,
  type ProfileResult,
  type ProfileOptions,
} from '@/api/modules/profile'
import {
  runValidation,
  type Validation,
  type ValidationRunOptions,
} from '@/api/modules/validations'
import {
  runPIIScan,
  type PIIScan,
  type PIIScanOptions,
} from '@/api/modules/privacy'
import {
  compareDrift,
  type DriftComparison,
  type DriftCompareRequest,
} from '@/api/modules/drift'
import { ApiError } from '@/api/core'

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

// Re-export types for convenience
export type {
  Source as DataSource,
  SourceType,
  SourceTypeDefinition,
  TestConnectionResult as ConnectionTestResult,
}

export interface TestConnectionRequest {
  type: SourceType
  config: Record<string, unknown>
}

export interface TestConnectionResponse {
  success: boolean
  connected: boolean
  message?: string
  error?: string
}

export interface CreateSourceRequest {
  name: string
  type: SourceType
  config: Record<string, unknown>
  description?: string
}

export interface UpdateSourceRequest {
  name?: string
  config?: Record<string, unknown>
  description?: string
  is_active?: boolean
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
      const response = await getSupportedSourceTypes()
      setState({ types: response.types, loading: false, error: null })
      return response.types
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
    getSupportedSourceTypes()
      .then((response) => {
        const definition = response.types.find((t) => t.type === type)
        if (definition) {
          setState({ data: definition, loading: false, error: null })
        } else {
          setState({ data: null, loading: false, error: new ApiError(404, 'Type not found') })
        }
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

export interface SourceListParams {
  search?: string
  type?: SourceType
  tags?: string[]
  page?: number
  page_size?: number
  offset?: number
  limit?: number
  active_only?: boolean
  sort_by?: 'name' | 'created_at' | 'updated_at' | 'type'
  sort_order?: 'asc' | 'desc'
}

/**
 * Hook for listing data sources with pagination and filtering.
 */
export function useSources(initialParams?: SourceListParams) {
  const [params, setParams] = useState<SourceListParams>(initialParams || {})
  const [state, setState] = useState<{
    sources: Source[]
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
      const response = await listSources({
        offset: fetchParams.offset,
        limit: fetchParams.limit,
        active_only: fetchParams.active_only,
      })
      setState({
        sources: response.data,
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
  const [state, setState] = useState<UseAsyncState<Source>>({
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
      const source = await getSource(id)
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
  const [state, setState] = useState<UseMutationState<Source>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const create = useCallback(async (data: CreateSourceRequest) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const source = await createSource(data)
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
  const [state, setState] = useState<UseMutationState<Source>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const update = useCallback(async (id: string, data: UpdateSourceRequest) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const source = await updateSource(id, data)
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
      await deleteSource(id)
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
      const result = await testConnectionConfig(request.type, request.config)
      const response: TestConnectionResponse = {
        success: result.connected,
        connected: result.connected,
        message: result.message,
        error: result.error,
      }
      setState({
        data: response,
        loading: false,
        error: null,
        success: result.connected,
      })
      return response
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error, success: false })
      return null
    }
  }, [])

  const testExisting = useCallback(async (id: string) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const result = await testSourceConnection(id)
      const response: TestConnectionResponse = {
        success: result.connected,
        connected: result.connected,
        message: result.message,
        error: result.error,
      }
      setState({
        data: response,
        loading: false,
        error: null,
        success: result.connected,
      })
      return response
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
  const [state, setState] = useState<UseAsyncState<Schema>>({
    data: null,
    loading: false,
    error: null,
  })

  const fetchSchema = useCallback(async () => {
    if (!sourceId) return null

    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const schema = await getSourceSchema(sourceId)
      setState({ data: schema, loading: false, error: null })
      return schema
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error })
      return null
    }
  }, [sourceId])

  const learn = useCallback(
    async (options?: { infer_constraints?: boolean; sample_size?: number }) => {
      if (!sourceId) return null

      setState((prev) => ({ ...prev, loading: true, error: null }))
      try {
        const schema = await learnSchema(sourceId, options)
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
    learn,
  }
}

/**
 * Hook for profile operations.
 */
export function useSourceProfile(sourceId: string | null) {
  const [state, setState] = useState<UseAsyncState<ProfileResult>>({
    data: null,
    loading: false,
    error: null,
  })

  const fetchProfile = useCallback(async () => {
    if (!sourceId) return null

    setState((prev) => ({ ...prev, loading: true, error: null }))
    try {
      const profile = await profileSource(sourceId)
      setState({ data: profile, loading: false, error: null })
      return profile
    } catch (err) {
      const error = err instanceof ApiError ? err : new ApiError(0, 'Unknown error')
      setState({ data: null, loading: false, error })
      return null
    }
  }, [sourceId])

  const runProfile = useCallback(
    async (options?: ProfileOptions) => {
      if (!sourceId) return null

      setState((prev) => ({ ...prev, loading: true, error: null }))
      try {
        const profile = await profileSource(sourceId, options)
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
  const [state, setState] = useState<UseMutationState<Validation>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const validate = useCallback(
    async (sourceId: string, options?: ValidationRunOptions) => {
      setState({ data: null, loading: true, error: null, success: false })
      try {
        const result = await runValidation(sourceId, options)
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
  const [state, setState] = useState<UseMutationState<DriftComparison>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const compare = useCallback(async (request: DriftCompareRequest) => {
    setState({ data: null, loading: true, error: null, success: false })
    try {
      const result = await compareDrift(request)
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
  const [state, setState] = useState<UseMutationState<PIIScan>>({
    data: null,
    loading: false,
    error: null,
    success: false,
  })

  const scan = useCallback(
    async (sourceId: string, options?: PIIScanOptions) => {
      setState({ data: null, loading: true, error: null, success: false })
      try {
        const result = await runPIIScan(sourceId, options)
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
  const { schema, loading: schemaLoading, learn: learnSchemaFn } = useSourceSchema(sourceId)
  const { profile, loading: profileLoading, run: runProfileFn } = useSourceProfile(sourceId)
  const { testExisting, loading: testLoading, data: testResult } = useConnectionTest()
  const { validate, loading: validating, data: validationResult } = useValidation()
  const { scan, loading: scanning, data: scanResult } = usePIIScan()

  const testConnection = useCallback(async () => {
    if (!sourceId) return null
    return testExisting(sourceId)
  }, [sourceId, testExisting])

  const runValidationFn = useCallback(
    async (options?: ValidationRunOptions) => {
      if (!sourceId) return null
      return validate(sourceId, options)
    },
    [sourceId, validate]
  )

  const runScan = useCallback(
    async (options?: PIIScanOptions) => {
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
    learnSchema: learnSchemaFn,

    // Profile
    profile,
    profileLoading,
    runProfile: runProfileFn,

    // Connection test
    testConnection,
    testLoading,
    testResult,

    // Validation
    runValidation: runValidationFn,
    validating,
    validationResult,

    // PII Scan
    runScan,
    scanning,
    scanResult,
  }
}
