/**
 * Profile API handlers
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById } from '../data/store'
import { createProfileResult } from '../factories'

const API_BASE = '/api/v1'

/**
 * Request body for profile endpoint
 */
interface ProfileRequest {
  sample_size?: number
}

export const profileHandlers = [
  // Profile a source
  http.post(`${API_BASE}/sources/:sourceId/profile`, async ({ params, request }) => {
    await delay(1200) // Simulate profiling time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Parse request body if present (sample_size support)
    let profileRequest: ProfileRequest | undefined
    try {
      const body = await request.text()
      if (body) {
        profileRequest = JSON.parse(body) as ProfileRequest
      }
    } catch {
      // Empty body or invalid JSON, continue without options
    }

    // Create profile result
    // In mock mode, sample_size doesn't actually affect the result,
    // but we acknowledge it was received for API compatibility
    const profile = createProfileResult({
      sourceName: source.name,
      // If sample_size is provided, simulate smaller dataset
      rowCount: profileRequest?.sample_size
        ? Math.min(profileRequest.sample_size, 1000000)
        : undefined,
    })

    return HttpResponse.json({
      success: true,
      data: profile,
    })
  }),
]
