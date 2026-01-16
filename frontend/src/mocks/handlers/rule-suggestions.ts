/**
 * Rule Suggestions API handlers
 */

import { http, HttpResponse, delay } from 'msw'
import { getStore, getById, getSchemaBySourceId } from '../data/store'
import {
  createRuleSuggestionResponse,
  createApplyRulesResponse,
  createContextualSuggestions,
  type SuggestedRule,
} from '../factories'

const API_BASE = '/api/v1'

// Store for generated suggestions (to support apply)
const suggestionsStore = new Map<string, SuggestedRule[]>()

export const ruleSuggestionsHandlers = [
  // Generate rule suggestions for a source
  http.post(`${API_BASE}/sources/:sourceId/rules/suggest`, async ({ params, request }) => {
    await delay(1000) // Simulate analysis time

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    // Parse request body for options
    interface SuggestRequest {
      profile_id?: string
      min_confidence?: number
    }

    let suggestOptions: SuggestRequest = {}
    try {
      const body = await request.json()
      suggestOptions = body as SuggestRequest
    } catch {
      // Empty body is fine, use defaults
    }

    // Get schema if available for contextual suggestions
    const schema = getSchemaBySourceId(sourceId)
    let response

    if (schema?.schema_json?.columns) {
      // Generate contextual suggestions based on schema
      const columns = Object.entries(schema.schema_json.columns).map(([name, col]: [string, any]) => ({
        name,
        dtype: col.dtype || 'object',
      }))

      const contextualSuggestions = createContextualSuggestions(columns)

      // Filter by min_confidence if provided
      const filteredSuggestions = suggestOptions.min_confidence
        ? contextualSuggestions.filter((s) => s.confidence >= suggestOptions.min_confidence!)
        : contextualSuggestions

      response = {
        source_id: sourceId,
        source_name: source.name,
        profile_id: suggestOptions.profile_id || 'mock-profile-id',
        total_suggestions: filteredSuggestions.length,
        high_confidence_count: filteredSuggestions.filter((s) => s.confidence >= 80).length,
        suggestions: filteredSuggestions,
        generated_at: new Date().toISOString(),
      }

      // Store for later apply
      suggestionsStore.set(sourceId, filteredSuggestions)
    } else {
      // Generate generic suggestions
      response = createRuleSuggestionResponse(sourceId, source.name, {
        profileId: suggestOptions.profile_id,
      })

      // Store for later apply
      suggestionsStore.set(sourceId, response.suggestions)
    }

    return HttpResponse.json(response)
  }),

  // Apply selected rule suggestions
  http.post(`${API_BASE}/sources/:sourceId/rules/apply-suggestions`, async ({ params, request }) => {
    await delay(500)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    interface ApplyRequest {
      suggestions?: SuggestedRule[]
      rule_ids?: string[]
      create_new_rule?: boolean
      rule_name?: string
    }

    let applyRequest: ApplyRequest
    try {
      applyRequest = (await request.json()) as ApplyRequest
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid request body' },
        { status: 400 }
      )
    }

    // Get stored suggestions
    const storedSuggestions = suggestionsStore.get(sourceId) ?? []

    // Support both suggestions array and rule_ids
    let selectedRules: SuggestedRule[]
    if (applyRequest.suggestions && applyRequest.suggestions.length > 0) {
      selectedRules = applyRequest.suggestions
    } else if (applyRequest.rule_ids && applyRequest.rule_ids.length > 0) {
      selectedRules = storedSuggestions.filter((s) =>
        applyRequest.rule_ids!.includes(s.id)
      )
    } else {
      return HttpResponse.json(
        { detail: 'suggestions or rule_ids is required' },
        { status: 400 }
      )
    }

    if (selectedRules.length === 0) {
      return HttpResponse.json(
        { detail: 'No valid rules found' },
        { status: 400 }
      )
    }

    const response = createApplyRulesResponse(sourceId, selectedRules)

    return HttpResponse.json(response)
  }),

  // Get previously generated suggestions (without re-analyzing)
  http.get(`${API_BASE}/sources/:sourceId/rules/suggestions`, async ({ params }) => {
    await delay(150)

    const sourceId = params.sourceId as string
    const source = getById(getStore().sources, sourceId)

    if (!source) {
      return HttpResponse.json(
        { detail: 'Source not found' },
        { status: 404 }
      )
    }

    const suggestions = suggestionsStore.get(sourceId)

    if (!suggestions) {
      return HttpResponse.json({
        source_id: sourceId,
        source_name: source.name,
        profile_id: null,
        suggestions: [],
        total_suggestions: 0,
        high_confidence_count: 0,
        generated_at: null,
      })
    }

    return HttpResponse.json({
      source_id: sourceId,
      source_name: source.name,
      profile_id: 'mock-profile-id',
      total_suggestions: suggestions.length,
      high_confidence_count: suggestions.filter((s) => s.confidence >= 0.8).length,
      suggestions,
      generated_at: new Date().toISOString(),
    })
  }),
]
