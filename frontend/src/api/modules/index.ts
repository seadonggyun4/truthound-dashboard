/**
 * API Modules - Re-export all domain modules.
 */

// Sources
export * from './sources'

// Validations
export * from './validations'

// Schemas
export * from './schemas'

// Profile
export * from './profile'

// History
export * from './history'

// Drift
export * from './drift'

// Schedules
export * from './schedules'

// Privacy (PII scan, masking)
export * from './privacy'

// Notifications (includes basic channels/rules/logs and advanced routing/deduplication/throttling/escalation)
export * from './notifications'

// Glossary
export * from './glossary'

// Catalog
export * from './catalog'

// Collaboration
export * from './collaboration'

// Validators
export * from './validators'

// Reports
export * from './reports'

// Maintenance
export * from './maintenance'

// Schema Evolution
export * from './schema-evolution'

// Rule Suggestions
export * from './rule-suggestions'

// Profile Comparison
export * from './profile-comparison'

// Versioning
export * from './versioning'

// Charts
export * from './charts'

// Lineage
export * from './lineage'

// Anomaly Detection
export * from './anomaly'

// Plugins
export * from './plugins'

// Triggers
export * from './triggers'

// Schema Watcher
export * from './schema-watcher'

// Enterprise Sampling
export * from './enterprise-sampling'

// Observability
// Note: HistogramBucket excluded to avoid conflict with profile module
export {
  type AuditEventType, type AuditStatus, type MetricType, type SpanKind, type SpanStatus,
  type ObservabilityConfig, type AuditEvent, type AuditEventListResponse, type AuditStats,
  type MetricValue, type HistogramValue, type SummaryQuantile, type SummaryValue,
  type MetricsResponse, type StoreMetrics, type SpanContext, type SpanEvent, type Span,
  type SpanListResponse, type TracingStats, type ObservabilityStats, type AuditQueryParams,
  getObservabilityConfig, updateObservabilityConfig, getObservabilityStats,
  listAuditEvents, getAuditStats, getMetrics, getStoreMetrics, getTracingStats, listSpans,
} from './observability'
