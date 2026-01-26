/**
 * Source management components
 *
 * Components for managing data sources including:
 * - Source type selection (File, Database, Warehouse, BigData, NoSQL, Streaming)
 * - Dynamic form rendering for connection configuration
 * - Connection testing with detailed feedback
 * - Source capability display
 *
 * Supports all source types from truthound's datasources module:
 * - File-based: CSV, Parquet, JSON, NDJSON, JSONL
 * - Core SQL: PostgreSQL, MySQL, SQLite
 * - Cloud DW: BigQuery, Snowflake, Redshift, Databricks
 * - Enterprise: Oracle, SQL Server
 * - Big Data: Apache Spark
 * - NoSQL: MongoDB, Elasticsearch
 * - Streaming: Apache Kafka, Kinesis
 */

export { AddSourceDialog } from './AddSourceDialog'
export { EditSourceDialog } from './EditSourceDialog'
export { SourceTypeSelector } from './SourceTypeSelector'
export { DynamicSourceForm } from './DynamicSourceForm'

// ConnectionTestResult and related components
export {
  ConnectionTestResult,
  TroubleshootingHints,
  type ConnectionTestResultData,
} from './ConnectionTestResult'

// SourceCapabilities and related components
export {
  SourceCapabilities,
  SourceCapabilitiesCompact,
  SourceCapabilitiesInline,
  SourceCapabilitiesList,
  CapabilityBadge,
  getCapabilityIcon,
  CAPABILITY_ICONS,
} from './SourceCapabilities'
