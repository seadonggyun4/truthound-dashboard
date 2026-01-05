/**
 * Drift detection API handlers
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getAll, getById, create } from '../data/store'
import { createDriftComparison, createId } from '../factories'

const API_BASE = '/api/v1'

export const driftHandlers = [
  // Compare drift between two sources
  http.post(`${API_BASE}/drift/compare`, async ({ request }) => {
    await delay(1500) // Simulate comparison time

    const body = (await request.json()) as {
      baseline_source_id: string
      current_source_id: string
      columns?: string[]
      method?: string
      threshold?: number
    }

    const baselineSource = getById(getStore().sources, body.baseline_source_id)
    const currentSource = getById(getStore().sources, body.current_source_id)

    if (!baselineSource) {
      return HttpResponse.json(
        { detail: 'Baseline source not found' },
        { status: 404 }
      )
    }

    if (!currentSource) {
      return HttpResponse.json(
        { detail: 'Current source not found' },
        { status: 404 }
      )
    }

    const comparison = createDriftComparison({
      id: createId(),
      baselineSourceId: body.baseline_source_id,
      currentSourceId: body.current_source_id,
    })

    create(getStore().driftComparisons, comparison)

    return HttpResponse.json({
      success: true,
      data: comparison,
    })
  }),

  // List drift comparisons
  http.get(`${API_BASE}/drift/comparisons`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const baselineSourceId = url.searchParams.get('baseline_source_id')
    const currentSourceId = url.searchParams.get('current_source_id')
    const limit = parseInt(url.searchParams.get('limit') ?? '20')

    let comparisons = getAll(getStore().driftComparisons)

    if (baselineSourceId) {
      comparisons = comparisons.filter(
        (c) => c.baseline_source_id === baselineSourceId
      )
    }

    if (currentSourceId) {
      comparisons = comparisons.filter(
        (c) => c.current_source_id === currentSourceId
      )
    }

    // Sort by created_at desc
    comparisons.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    const paginated = comparisons.slice(0, limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total: comparisons.length,
    })
  }),

  // Get drift comparison by ID
  http.get(`${API_BASE}/drift/comparisons/:id`, async ({ params }) => {
    await delay(150)

    const comparison = getById(getStore().driftComparisons, params.id as string)

    if (!comparison) {
      return HttpResponse.json(
        { detail: 'Drift comparison not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({
      success: true,
      data: comparison,
    })
  }),
]
