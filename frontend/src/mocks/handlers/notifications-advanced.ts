/**
 * Advanced Notifications API handlers
 * Handles routing rules, deduplication, throttling, and escalation endpoints
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
import {
  createRoutingRule,
  createDeduplicationConfig,
  createThrottlingConfig,
  createEscalationPolicy,
  createDeduplicationStats,
  createThrottlingStats,
  createEscalationStats,
  getRuleTypes,
  createId,
  type RoutingRule,
  type DeduplicationConfig,
  type ThrottlingConfig,
  type EscalationPolicy,
} from '../factories'

const API_BASE = '/api/v1'

export const notificationsAdvancedHandlers = [
  // ============================================================================
  // Routing Rules
  // ============================================================================

  // Get rule types
  http.get(`${API_BASE}/notifications/routing/rules/types`, async () => {
    await delay(100)

    return HttpResponse.json({
      rule_types: getRuleTypes(),
    })
  }),

  // List routing rules
  http.get(`${API_BASE}/notifications/routing/rules`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'

    let rules = getAll(getStore().routingRules)

    if (activeOnly) {
      rules = rules.filter((r) => r.is_active)
    }

    // Sort by priority descending
    rules.sort((a, b) => b.priority - a.priority)

    const total = rules.length
    const paginated = rules.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get routing rule by ID
  http.get(`${API_BASE}/notifications/routing/rules/:id`, async ({ params }) => {
    await delay(150)

    const rule = getById(getStore().routingRules, params.id as string)

    if (!rule) {
      return HttpResponse.json(
        { detail: 'Routing rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(rule)
  }),

  // Create routing rule
  http.post(`${API_BASE}/notifications/routing/rules`, async ({ request }) => {
    await delay(300)

    let body: Partial<RoutingRule>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const rule = createRoutingRule({
      id: createId(),
      name: body.name,
      channelIds: body.actions,
      priority: body.priority,
      isActive: body.is_active,
    })

    if (body.rule_config) {
      rule.rule_config = body.rule_config
    }
    if (body.stop_on_match !== undefined) {
      rule.stop_on_match = body.stop_on_match
    }
    if (body.metadata) {
      rule.metadata = body.metadata
    }

    rule.created_at = new Date().toISOString()
    rule.updated_at = new Date().toISOString()

    create(getStore().routingRules, rule)

    return HttpResponse.json(rule)
  }),

  // Update routing rule
  http.put(`${API_BASE}/notifications/routing/rules/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<RoutingRule>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().routingRules,
      params.id as string,
      { ...body, updated_at: new Date().toISOString() }
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Routing rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete routing rule
  http.delete(`${API_BASE}/notifications/routing/rules/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().routingRules, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Routing rule not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true, message: 'Routing rule deleted' })
  }),

  // ============================================================================
  // Deduplication
  // ============================================================================

  // List deduplication configs
  http.get(`${API_BASE}/notifications/deduplication/configs`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'

    let configs = getAll(getStore().deduplicationConfigs)

    if (activeOnly) {
      configs = configs.filter((c) => c.is_active)
    }

    const total = configs.length
    const paginated = configs.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get deduplication config by ID
  http.get(`${API_BASE}/notifications/deduplication/configs/:id`, async ({ params }) => {
    await delay(150)

    const config = getById(getStore().deduplicationConfigs, params.id as string)

    if (!config) {
      return HttpResponse.json(
        { detail: 'Deduplication config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(config)
  }),

  // Create deduplication config
  http.post(`${API_BASE}/notifications/deduplication/configs`, async ({ request }) => {
    await delay(300)

    let body: Partial<DeduplicationConfig>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const config = createDeduplicationConfig({
      id: createId(),
      name: body.name,
      strategy: body.strategy,
      policy: body.policy,
      windowSeconds: body.window_seconds,
      isActive: body.is_active,
    })

    config.created_at = new Date().toISOString()
    config.updated_at = new Date().toISOString()

    create(getStore().deduplicationConfigs, config)

    return HttpResponse.json(config)
  }),

  // Update deduplication config
  http.put(`${API_BASE}/notifications/deduplication/configs/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<DeduplicationConfig>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().deduplicationConfigs,
      params.id as string,
      { ...body, updated_at: new Date().toISOString() }
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Deduplication config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete deduplication config
  http.delete(`${API_BASE}/notifications/deduplication/configs/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().deduplicationConfigs, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Deduplication config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true, message: 'Deduplication config deleted' })
  }),

  // Get deduplication stats
  http.get(`${API_BASE}/notifications/deduplication/stats`, async () => {
    await delay(150)

    return HttpResponse.json(createDeduplicationStats())
  }),

  // ============================================================================
  // Throttling
  // ============================================================================

  // List throttling configs
  http.get(`${API_BASE}/notifications/throttling/configs`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'
    const channelId = url.searchParams.get('channel_id')

    let configs = getAll(getStore().throttlingConfigs)

    if (activeOnly) {
      configs = configs.filter((c) => c.is_active)
    }

    if (channelId) {
      configs = configs.filter((c) => c.channel_id === channelId)
    }

    const total = configs.length
    const paginated = configs.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get throttling config by ID
  http.get(`${API_BASE}/notifications/throttling/configs/:id`, async ({ params }) => {
    await delay(150)

    const config = getById(getStore().throttlingConfigs, params.id as string)

    if (!config) {
      return HttpResponse.json(
        { detail: 'Throttling config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(config)
  }),

  // Create throttling config
  http.post(`${API_BASE}/notifications/throttling/configs`, async ({ request }) => {
    await delay(300)

    let body: Partial<ThrottlingConfig>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const config = createThrottlingConfig({
      id: createId(),
      name: body.name,
      perMinute: body.per_minute,
      perHour: body.per_hour,
      perDay: body.per_day,
      burstAllowance: body.burst_allowance,
      channelId: body.channel_id,
      isActive: body.is_active,
    })

    config.created_at = new Date().toISOString()
    config.updated_at = new Date().toISOString()

    create(getStore().throttlingConfigs, config)

    return HttpResponse.json(config)
  }),

  // Update throttling config
  http.put(`${API_BASE}/notifications/throttling/configs/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<ThrottlingConfig>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().throttlingConfigs,
      params.id as string,
      { ...body, updated_at: new Date().toISOString() }
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Throttling config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete throttling config
  http.delete(`${API_BASE}/notifications/throttling/configs/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().throttlingConfigs, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Throttling config not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true, message: 'Throttling config deleted' })
  }),

  // Get throttling stats
  http.get(`${API_BASE}/notifications/throttling/stats`, async () => {
    await delay(150)

    return HttpResponse.json(createThrottlingStats())
  }),

  // ============================================================================
  // Escalation Policies
  // ============================================================================

  // List escalation policies
  http.get(`${API_BASE}/notifications/escalation/policies`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const activeOnly = url.searchParams.get('active_only') === 'true'

    let policies = getAll(getStore().escalationPolicies)

    if (activeOnly) {
      policies = policies.filter((p) => p.is_active)
    }

    const total = policies.length
    const paginated = policies.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get escalation policy by ID
  http.get(`${API_BASE}/notifications/escalation/policies/:id`, async ({ params }) => {
    await delay(150)

    const policy = getById(getStore().escalationPolicies, params.id as string)

    if (!policy) {
      return HttpResponse.json(
        { detail: 'Escalation policy not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(policy)
  }),

  // Create escalation policy
  http.post(`${API_BASE}/notifications/escalation/policies`, async ({ request }) => {
    await delay(300)

    let body: Partial<EscalationPolicy>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const policy = createEscalationPolicy({
      id: createId(),
      name: body.name,
      levelCount: body.levels?.length,
      isActive: body.is_active,
    })

    if (body.description) policy.description = body.description
    if (body.levels) policy.levels = body.levels
    if (body.auto_resolve_on_success !== undefined) policy.auto_resolve_on_success = body.auto_resolve_on_success
    if (body.max_escalations) policy.max_escalations = body.max_escalations

    policy.created_at = new Date().toISOString()
    policy.updated_at = new Date().toISOString()

    create(getStore().escalationPolicies, policy)

    return HttpResponse.json(policy)
  }),

  // Update escalation policy
  http.put(`${API_BASE}/notifications/escalation/policies/:id`, async ({ params, request }) => {
    await delay(250)

    let body: Partial<EscalationPolicy>

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const updated = update(
      getStore().escalationPolicies,
      params.id as string,
      { ...body, updated_at: new Date().toISOString() }
    )

    if (!updated) {
      return HttpResponse.json(
        { detail: 'Escalation policy not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(updated)
  }),

  // Delete escalation policy
  http.delete(`${API_BASE}/notifications/escalation/policies/:id`, async ({ params }) => {
    await delay(200)

    const deleted = remove(getStore().escalationPolicies, params.id as string)

    if (!deleted) {
      return HttpResponse.json(
        { detail: 'Escalation policy not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json({ success: true, message: 'Escalation policy deleted' })
  }),

  // ============================================================================
  // Escalation Incidents
  // ============================================================================

  // List escalation incidents
  http.get(`${API_BASE}/notifications/escalation/incidents`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')
    const policyId = url.searchParams.get('policy_id')
    const state = url.searchParams.get('state')

    let incidents = getAll(getStore().escalationIncidents)

    if (policyId) {
      incidents = incidents.filter((i) => i.policy_id === policyId)
    }

    if (state) {
      incidents = incidents.filter((i) => i.state === state)
    }

    // Sort by created_at descending
    incidents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    const total = incidents.length
    const paginated = incidents.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // List active incidents
  http.get(`${API_BASE}/notifications/escalation/incidents/active`, async ({ request }) => {
    await delay(200)

    const url = new URL(request.url)
    const offset = parseInt(url.searchParams.get('offset') ?? '0')
    const limit = parseInt(url.searchParams.get('limit') ?? '50')

    let incidents = getAll(getStore().escalationIncidents)
      .filter((i) => i.state !== 'resolved')

    // Sort by created_at descending
    incidents.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    const total = incidents.length
    const paginated = incidents.slice(offset, offset + limit)

    return HttpResponse.json({
      items: paginated,
      total,
      offset,
      limit,
    })
  }),

  // Get escalation incident by ID
  http.get(`${API_BASE}/notifications/escalation/incidents/:id`, async ({ params }) => {
    await delay(150)

    const incident = getById(getStore().escalationIncidents, params.id as string)

    if (!incident) {
      return HttpResponse.json(
        { detail: 'Escalation incident not found' },
        { status: 404 }
      )
    }

    return HttpResponse.json(incident)
  }),

  // Acknowledge incident
  http.post(`${API_BASE}/notifications/escalation/incidents/:id/acknowledge`, async ({ params, request }) => {
    await delay(300)

    let body: { actor: string; message?: string }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const incident = getById(getStore().escalationIncidents, params.id as string)

    if (!incident) {
      return HttpResponse.json(
        { detail: 'Escalation incident not found' },
        { status: 404 }
      )
    }

    if (incident.state === 'resolved') {
      return HttpResponse.json(
        { detail: 'Cannot acknowledge resolved incident' },
        { status: 400 }
      )
    }

    if (incident.state === 'acknowledged') {
      return HttpResponse.json(
        { detail: 'Incident already acknowledged' },
        { status: 400 }
      )
    }

    const oldState = incident.state
    const now = new Date().toISOString()

    incident.state = 'acknowledged'
    incident.acknowledged_by = body.actor
    incident.acknowledged_at = now
    incident.updated_at = now
    incident.events.push({
      from_state: oldState,
      to_state: 'acknowledged',
      actor: body.actor,
      message: body.message ?? `Acknowledged by ${body.actor}`,
      timestamp: now,
    })

    update(getStore().escalationIncidents, incident.id, incident)

    return HttpResponse.json(incident)
  }),

  // Resolve incident
  http.post(`${API_BASE}/notifications/escalation/incidents/:id/resolve`, async ({ params, request }) => {
    await delay(300)

    let body: { actor?: string; message?: string }

    try {
      body = await request.json() as typeof body
    } catch {
      return HttpResponse.json(
        { detail: 'Invalid JSON in request body' },
        { status: 400 }
      )
    }

    const incident = getById(getStore().escalationIncidents, params.id as string)

    if (!incident) {
      return HttpResponse.json(
        { detail: 'Escalation incident not found' },
        { status: 404 }
      )
    }

    if (incident.state === 'resolved') {
      return HttpResponse.json(
        { detail: 'Incident already resolved' },
        { status: 400 }
      )
    }

    const oldState = incident.state
    const now = new Date().toISOString()
    const actor = body.actor ?? 'system'

    incident.state = 'resolved'
    incident.resolved_by = body.actor ?? null
    incident.resolved_at = now
    incident.next_escalation_at = null
    incident.updated_at = now
    incident.events.push({
      from_state: oldState,
      to_state: 'resolved',
      actor: body.actor ?? null,
      message: body.message ?? `Resolved by ${actor}`,
      timestamp: now,
    })

    update(getStore().escalationIncidents, incident.id, incident)

    return HttpResponse.json(incident)
  }),

  // Get escalation stats
  http.get(`${API_BASE}/notifications/escalation/stats`, async () => {
    await delay(150)

    const policies = getAll(getStore().escalationPolicies)

    return HttpResponse.json(createEscalationStats(policies.length))
  }),
]
