/**
 * Sources API handlers
 */

import { http, HttpResponse, delay } from 'msw'
import {
  getStore,
  getAll,
  getById,
  create,
  update,
  remove,
} from '../data/store'
import { createSource, createId } from '../factories'

const API_BASE = '/api/v1'

export const sourcesHandlers = [
  // List sources
  http.get(`${API_BASE}/sources`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'

    let sources = getAll(getStore().sources)

    if (activeOnly) {
      sources = sources.filter((s) => s.is_active)
    }

    // Sort by created_at desc
    sources.sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    const total = sources.length
    const paginated = sources.slice(offset, offset + limit)

    return HttpResponse.json({
      success: true,
      data: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get source by ID
  http.get(`${API_BASE}/sources/:id`, async ({ params }) => {
    await delay(150)

    const source = getById(getStore().sources, params.id as string)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(source)
  }),

  // Create source
  http.post(`${API_BASE}/sources`, async ({ request }) => {
    await delay(300)

    const body = (await request.json()) as {
      name: string
      type: string
      config: Record<string, unknown>
      description?: string
    }

    const newSource = createSource({
      id: createId(),
      name: body.name,
      type: body.type,
    })

    newSource.config = body.config
    newSource.description = body.description
    newSource.created_at = new Date().toISOString()
    newSource.updated_at = new Date().toISOString()

    create(getStore().sources, newSource)

    return HttpResponse.json(newSource, { status: 201 })
  }),

  // Update source
  http.put(`${API_BASE}/sources/:id`, async ({ params, request }) => {
    await delay(250)

    const body = (await request.json()) as Partial<{
      name: string
      config: Record<string, unknown>
      description: string
      is_active: boolean
    }>

    const updated = update(getStore().sources, params.id as string, body)

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete source
  http.delete(`${API_BASE}/sources/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().sources, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ message: 'Source deleted successfully' })
  }),

  // Test source connection
  http.post(`${API_BASE}/sources/:id/test`, async ({ params }) => {
    await delay(500)

    const source = getById(getStore().sources, params.id as string)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Simulate 90% success rate
    const success = Math.random() > 0.1

    return HttpResponse.json({
      success: true,
      data: {
        success,
        message: success ? 'Connection successful' : undefined,
        error: success ? undefined : 'Connection timeout after 30s',
      },
    })
  }),

  // Get supported source types
  http.get(`${API_BASE}/sources/types/supported`, async () => {
    await delay(100)

    return HttpResponse.json({
      success: true,
      data: [
        {
          type: 'csv',
          name: 'CSV File',
          description: 'Comma-separated values file',
          required_fields: ['path'],
          optional_fields: ['delimiter', 'encoding', 'header'],
        },
        {
          type: 'parquet',
          name: 'Parquet File',
          description: 'Apache Parquet columnar format',
          required_fields: ['path'],
          optional_fields: [],
        },
        {
          type: 'excel',
          name: 'Excel File',
          description: 'Microsoft Excel spreadsheet',
          required_fields: ['path'],
          optional_fields: ['sheet', 'range'],
        },
        {
          type: 'json',
          name: 'JSON File',
          description: 'JSON or JSON Lines file',
          required_fields: ['path'],
          optional_fields: ['lines'],
        },
        {
          type: 'database',
          name: 'Database',
          description: 'SQL Database connection',
          required_fields: ['connection_string', 'table'],
          optional_fields: ['schema', 'query'],
        },
      ],
    })
  }),
]
