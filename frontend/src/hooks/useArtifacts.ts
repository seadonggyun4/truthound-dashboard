import { useCallback, useEffect, useState } from 'react'

import {
  cleanupExpiredArtifacts,
  deleteArtifact,
  getArtifactStatistics,
  listArtifacts,
  type ArtifactRecord,
  type ArtifactStatistics,
  type ArtifactFormat,
  type ArtifactStatus,
} from '@/api/modules/artifacts'
import { useToast } from '@/hooks/use-toast'

interface ArtifactQuery {
  workspace_id?: string
  saved_view_id?: string
  search?: string
  status?: ArtifactStatus
  source_id?: string
  validation_id?: string
  artifact_type?: string
  format?: ArtifactFormat
  include_expired?: boolean
  offset?: number
  limit?: number
}

interface UseArtifactIndexOptions {
  query?: ArtifactQuery
  autoFetch?: boolean
}

interface UseArtifactIndexResult {
  artifacts: ArtifactRecord[]
  total: number
  page: number
  pageSize: number
  statistics: ArtifactStatistics | null
  isLoading: boolean
  error: Error | null
  refetch: () => Promise<void>
  fetchStatistics: () => Promise<void>
  setPage: (page: number) => void
  setPageSize: (size: number) => void
  updateQuery: (query: Partial<ArtifactQuery>) => void
  deleteArtifactRecord: (artifactId: string) => Promise<void>
  cleanupExpired: () => Promise<number>
}

export function useArtifactIndex(
  options: UseArtifactIndexOptions = {}
): UseArtifactIndexResult {
  const { toast } = useToast()
  const { query: initialQuery, autoFetch = true } = options

  const [artifacts, setArtifacts] = useState<ArtifactRecord[]>([])
  const [total, setTotal] = useState(0)
  const [statistics, setStatistics] = useState<ArtifactStatistics | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [query, setQuery] = useState<ArtifactQuery>({
    offset: 0,
    limit: 20,
    ...initialQuery,
  })

  const fetchArtifacts = useCallback(async () => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await listArtifacts(query)
      setArtifacts(response.data ?? [])
      setTotal(response.total ?? 0)
    } catch (err) {
      const nextError = err instanceof Error ? err : new Error('Failed to fetch artifacts')
      setError(nextError)
    } finally {
      setIsLoading(false)
    }
  }, [query])

  const fetchStatistics = useCallback(async () => {
    try {
      const stats = await getArtifactStatistics()
      setStatistics(stats)
    } catch (err) {
      console.error('Failed to fetch artifact statistics:', err)
    }
  }, [])

  useEffect(() => {
    if (autoFetch) {
      void fetchArtifacts()
      void fetchStatistics()
    }
  }, [autoFetch, fetchArtifacts, fetchStatistics])

  const setPage = useCallback((page: number) => {
    setQuery((prev) => ({
      ...prev,
      offset: Math.max(0, page - 1) * (prev.limit ?? 20),
    }))
  }, [])

  const setPageSize = useCallback((limit: number) => {
    setQuery((prev) => ({
      ...prev,
      limit,
      offset: 0,
    }))
  }, [])

  const updateQuery = useCallback((nextQuery: Partial<ArtifactQuery>) => {
    setQuery((prev) => ({
      ...prev,
      ...nextQuery,
      offset: nextQuery.offset ?? 0,
    }))
  }, [])

  const deleteArtifactRecord = useCallback(async (artifactId: string) => {
    try {
      await deleteArtifact(artifactId)
      toast({
        title: 'Artifact Deleted',
        description: 'The artifact has been deleted successfully',
      })
      await fetchArtifacts()
      await fetchStatistics()
    } catch (err) {
      const nextError = err instanceof Error ? err : new Error('Delete failed')
      toast({
        title: 'Delete Failed',
        description: nextError.message,
        variant: 'destructive',
      })
      throw nextError
    }
  }, [fetchArtifacts, fetchStatistics, toast])

  const handleCleanupExpired = useCallback(async () => {
    try {
      const result = await cleanupExpiredArtifacts()
      toast({
        title: 'Cleanup Complete',
        description: `Deleted ${result.deleted} expired artifacts`,
      })
      await fetchArtifacts()
      await fetchStatistics()
      return result.deleted
    } catch (err) {
      const nextError = err instanceof Error ? err : new Error('Cleanup failed')
      toast({
        title: 'Cleanup Failed',
        description: nextError.message,
        variant: 'destructive',
      })
      throw nextError
    }
  }, [fetchArtifacts, fetchStatistics, toast])

  const page = Math.floor((query.offset ?? 0) / (query.limit ?? 20)) + 1

  return {
    artifacts,
    total,
    page,
    pageSize: query.limit ?? 20,
    statistics,
    isLoading,
    error,
    refetch: fetchArtifacts,
    fetchStatistics,
    setPage,
    setPageSize,
    updateQuery,
    deleteArtifactRecord,
    cleanupExpired: handleCleanupExpired,
  }
}
