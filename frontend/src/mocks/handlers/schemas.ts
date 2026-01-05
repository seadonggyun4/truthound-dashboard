/**
 * Schema API handlers
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById, getSchemaBySourceId } from '../data/store'
import { createSchema, createId } from '../factories'

const API_BASE = '/api/v1'

export const schemasHandlers = [
  // Get schema for a source
  http.get(`${API_BASE}/sources/:sourceId/schema`, async ({ params }) => {
    await delay(150)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const schema = getSchemaBySourceId(sourceId)

    if (!schema) {
      return HttpResponse.json(null)
    }

    return HttpResponse.json(schema)
  }),

  // Learn schema for a source
  http.post(`${API_BASE}/sources/:sourceId/learn`, async ({ params }) => {
    await delay(1000) // Simulate learning time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Create or update schema
    const schema = createSchema({
      id: createId(),
      sourceId,
    })

    getStore().schemas.set(sourceId, schema)

    // Update source's has_schema flag
    const sources = getStore().sources
    sources.set(sourceId, { ...source, has_schema: true })

    return HttpResponse.json(schema)
  }),

  // Update schema
  http.put(`${API_BASE}/sources/:sourceId/schema`, async ({ params, request }) => {
    await delay(300)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const body = (await request.json()) as { schema_yaml: string }

    const existingSchema = getSchemaBySourceId(sourceId)

    const updatedSchema = {
      ...(existingSchema ?? createSchema({ sourceId })),
      schema_yaml: body.schema_yaml,
      updated_at: new Date().toISOString(),
    }

    getStore().schemas.set(sourceId, updatedSchema)

    return HttpResponse.json(updatedSchema)
  }),
]
