/**
 * Zustand store for lineage data.
 *
 * Persists lineage graph data across page navigation to prevent
 * unnecessary API calls and re-renders.
 *
 * Features:
 * - Caching with configurable TTL
 * - Request deduplication (prevents concurrent duplicate requests)
 * - Optimistic updates for add/remove operations
 */

import { create } from 'zustand'
import {
  getLineageGraph,
  type LineageGraph,
  type LineageNode,
} from '@/api/modules/lineage'
import { deduplicatedRequest } from '@/lib/request-utils'

interface LineageStore {
  // Data
  lineageData: LineageGraph | null
  isLoading: boolean
  error: string | null
  lastFetchedAt: number | null

  // Actions
  fetchLineageData: (force?: boolean) => Promise<void>
  setLineageData: (data: LineageGraph | null) => void
  addNode: (node: LineageNode) => void
  removeNode: (nodeId: string) => void
  reset: () => void
}

// Cache duration: 5 minutes
const CACHE_DURATION = 5 * 60 * 1000

// Request key for deduplication
const LINEAGE_REQUEST_KEY = 'lineage-graph'

export const useLineageStore = create<LineageStore>((set, get) => ({
  // Initial state
  lineageData: null,
  isLoading: false,
  error: null,
  lastFetchedAt: null,

  // Fetch lineage data with caching and deduplication
  fetchLineageData: async (force = false) => {
    const { lastFetchedAt, isLoading, lineageData } = get()

    // Skip if already loading (handled by deduplication, but early exit is faster)
    if (isLoading) return

    // Skip if cache is still valid (unless forced)
    if (
      !force &&
      lineageData &&
      lastFetchedAt &&
      Date.now() - lastFetchedAt < CACHE_DURATION
    ) {
      return
    }

    set({ isLoading: true, error: null })

    try {
      // Use deduplication to prevent concurrent requests
      const data = await deduplicatedRequest(LINEAGE_REQUEST_KEY, getLineageGraph)
      set({
        lineageData: data,
        isLoading: false,
        lastFetchedAt: Date.now(),
      })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load lineage data',
        isLoading: false,
      })
    }
  },

  // Direct setter for optimistic updates
  setLineageData: (data) => set({ lineageData: data }),

  // Add a node (optimistic update)
  addNode: (node) => {
    const { lineageData } = get()
    if (!lineageData) return

    set({
      lineageData: {
        ...lineageData,
        nodes: [...lineageData.nodes, node],
        total_nodes: lineageData.total_nodes + 1,
      },
    })
  },

  // Remove a node (optimistic update)
  removeNode: (nodeId) => {
    const { lineageData } = get()
    if (!lineageData) return

    set({
      lineageData: {
        ...lineageData,
        nodes: lineageData.nodes.filter((n) => n.id !== nodeId),
        edges: lineageData.edges.filter(
          (e) => e.source_node_id !== nodeId && e.target_node_id !== nodeId
        ),
        total_nodes: lineageData.total_nodes - 1,
      },
    })
  },

  // Reset store
  reset: () =>
    set({
      lineageData: null,
      isLoading: false,
      error: null,
      lastFetchedAt: null,
    }),
}))
