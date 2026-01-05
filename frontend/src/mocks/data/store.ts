/**
 * In-memory data store for mock API
 * Provides CRUD operations with persistence during session
 */

import type {
  Source,
  Validation,
  Schema,
  Schedule,
  DriftComparison,
  NotificationChannel,
  NotificationRule,
  NotificationLog,
} from '@/api/client'
import {
  createSources,
  createValidations,
  createSchema,
  createSchedules,
  createDriftComparisons,
  createNotificationChannels,
  createNotificationRules,
  createNotificationLogs,
} from '../factories'

// ============================================================================
// Store State
// ============================================================================

interface MockStore {
  sources: Map<string, Source>
  validations: Map<string, Validation>
  schemas: Map<string, Schema> // keyed by source_id
  schedules: Map<string, Schedule>
  driftComparisons: Map<string, DriftComparison>
  notificationChannels: Map<string, NotificationChannel>
  notificationRules: Map<string, NotificationRule>
  notificationLogs: Map<string, NotificationLog>
}

let store: MockStore | null = null

// ============================================================================
// Initialize Store
// ============================================================================

function initializeStore(): MockStore {
  // Create initial sources
  const sources = createSources(8)
  const sourcesMap = new Map(sources.map((s) => [s.id, s]))

  // Create validations for each source
  const validations: Validation[] = []
  sources.forEach((source) => {
    const sourceValidations = createValidations(5, source.id)
    validations.push(...sourceValidations)
  })
  const validationsMap = new Map(validations.map((v) => [v.id, v]))

  // Create schemas for sources with has_schema = true
  const schemasMap = new Map<string, Schema>()
  sources.filter((s) => s.has_schema).forEach((source) => {
    const schema = createSchema({ sourceId: source.id })
    schemasMap.set(source.id, schema)
  })

  // Create schedules linked to sources
  const schedules = createSchedules(5).map((schedule, i) => ({
    ...schedule,
    source_id: sources[i % sources.length].id,
    source_name: sources[i % sources.length].name,
  }))
  const schedulesMap = new Map(schedules.map((s) => [s.id, s]))

  // Create drift comparisons
  const driftComparisons = createDriftComparisons(6).map((drift, i) => ({
    ...drift,
    baseline_source_id: sources[i % sources.length].id,
    current_source_id: sources[(i + 1) % sources.length].id,
  }))
  const driftComparisonsMap = new Map(driftComparisons.map((d) => [d.id, d]))

  // Create notification channels
  const channels = createNotificationChannels(4)
  const channelsMap = new Map(channels.map((c) => [c.id, c]))

  // Create notification rules linked to channels
  const rules = createNotificationRules(5).map((rule) => ({
    ...rule,
    channel_ids: [channels[0].id, channels[1].id].slice(0, Math.random() > 0.5 ? 2 : 1),
  }))
  const rulesMap = new Map(rules.map((r) => [r.id, r]))

  // Create notification logs
  const logs = createNotificationLogs(20).map((log) => ({
    ...log,
    channel_id: channels[Math.floor(Math.random() * channels.length)].id,
  }))
  const logsMap = new Map(logs.map((l) => [l.id, l]))

  return {
    sources: sourcesMap,
    validations: validationsMap,
    schemas: schemasMap,
    schedules: schedulesMap,
    driftComparisons: driftComparisonsMap,
    notificationChannels: channelsMap,
    notificationRules: rulesMap,
    notificationLogs: logsMap,
  }
}

// ============================================================================
// Store Access
// ============================================================================

export function getStore(): MockStore {
  if (!store) {
    store = initializeStore()
  }
  return store
}

export function resetStore(): void {
  store = initializeStore()
}

// ============================================================================
// Generic CRUD Helpers
// ============================================================================

export function getAll<T>(map: Map<string, T>): T[] {
  return Array.from(map.values())
}

export function getById<T>(map: Map<string, T>, id: string): T | undefined {
  return map.get(id)
}

export function create<T extends { id: string }>(map: Map<string, T>, item: T): T {
  map.set(item.id, item)
  return item
}

export function update<T extends { id: string }>(
  map: Map<string, T>,
  id: string,
  updates: Partial<T>
): T | undefined {
  const existing = map.get(id)
  if (!existing) return undefined

  const updated = { ...existing, ...updates, updated_at: new Date().toISOString() }
  map.set(id, updated)
  return updated
}

export function remove<T>(map: Map<string, T>, id: string): boolean {
  return map.delete(id)
}

// ============================================================================
// Specific Query Helpers
// ============================================================================

export function getValidationsBySourceId(sourceId: string): Validation[] {
  return getAll(getStore().validations)
    .filter((v) => v.source_id === sourceId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}

export function getSchemaBySourceId(sourceId: string): Schema | undefined {
  return getStore().schemas.get(sourceId)
}

export function getSchedulesBySourceId(sourceId: string): Schedule[] {
  return getAll(getStore().schedules).filter((s) => s.source_id === sourceId)
}

export function getLogsByChannelId(channelId: string): NotificationLog[] {
  return getAll(getStore().notificationLogs)
    .filter((l) => l.channel_id === channelId)
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
}
