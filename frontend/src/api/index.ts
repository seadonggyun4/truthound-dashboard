/**
 * Truthound Dashboard API Client - Modular Structure
 *
 * Organized by domain for better maintainability.
 *
 * @example
 * // Import specific functions from modules
 * import { listSources, runValidation, getProfile } from '@/api/modules/sources'
 *
 * // Import from specific modules
 * import * as sources from '@/api/modules/sources'
 * import * as validations from '@/api/modules/validations'
 */

// Core exports - base request function and common types
export { request, ApiError, getHealth } from './core'
export type { RequestOptions, PaginatedResponse, MessageResponse, OkResponse, HealthResponse } from './core'

// Module re-exports - organized by domain
export * as sources from './modules/sources'
export * as validations from './modules/validations'
export * as schemas from './modules/schemas'
export * as profile from './modules/profile'
export * as history from './modules/history'
export * as drift from './modules/drift'
export * as schedules from './modules/schedules'
export * as privacy from './modules/privacy'
export * as notifications from './modules/notifications'
export * as glossary from './modules/glossary'
export * as catalog from './modules/catalog'
export * as collaboration from './modules/collaboration'
export * as validators from './modules/validators'
export * as reports from './modules/reports'
export * as maintenance from './modules/maintenance'
export * as schemaEvolution from './modules/schema-evolution'
export * as ruleSuggestions from './modules/rule-suggestions'
export * as profileComparison from './modules/profile-comparison'
export * as versioning from './modules/versioning'
export * as charts from './modules/charts'
export * as lineage from './modules/lineage'
export * as anomaly from './modules/anomaly'
export * as plugins from './modules/plugins'
export * as triggers from './modules/triggers'
