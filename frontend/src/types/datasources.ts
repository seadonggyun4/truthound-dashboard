/**
 * DataSource types and definitions
 *
 * Based on truthound framework datasources module.
 * Supports multiple backends: files, SQL databases, cloud warehouses, NoSQL, streaming.
 */

// ============================================================================
// Source Type Enums
// ============================================================================

/**
 * All supported source types mapped to truthound datasources.
 */
export type SourceType =
  // File-based
  | 'file'
  | 'csv'
  | 'parquet'
  | 'json'
  | 'ndjson'
  | 'jsonl'
  // DataFrame
  | 'polars'
  | 'pandas'
  // Core SQL
  | 'sqlite'
  | 'postgresql'
  | 'mysql'
  // Cloud Data Warehouses
  | 'bigquery'
  | 'snowflake'
  | 'redshift'
  | 'databricks'
  // Enterprise
  | 'oracle'
  | 'sqlserver'
  // NoSQL (async)
  | 'mongodb'
  | 'elasticsearch'
  // Streaming (async)
  | 'kafka'
  | 'kinesis'
  // Big Data
  | 'spark'

/**
 * Source type categories for UI grouping.
 */
export type SourceCategory =
  | 'file'
  | 'dataframe'
  | 'database'
  | 'warehouse'
  | 'enterprise'
  | 'nosql'
  | 'streaming'
  | 'bigdata'

/**
 * Data source capabilities from truthound.datasources.DataSourceCapability.
 */
export type DataSourceCapability =
  | 'lazy_evaluation'    // Supports lazy/deferred execution
  | 'sql_pushdown'       // Can push operations to database
  | 'sampling'           // Supports efficient sampling
  | 'streaming'          // Supports streaming/chunked reads
  | 'schema_inference'   // Can infer schema without full scan
  | 'row_count'          // Can get row count efficiently

/**
 * Column types from truthound.datasources.ColumnType.
 */
export type ColumnType =
  | 'integer'
  | 'float'
  | 'decimal'
  | 'string'
  | 'text'
  | 'date'
  | 'datetime'
  | 'time'
  | 'duration'
  | 'boolean'
  | 'binary'
  | 'list'
  | 'struct'
  | 'json'
  | 'null'
  | 'unknown'

// ============================================================================
// Configuration Interfaces
// ============================================================================

/**
 * Base configuration for all data sources.
 * Maps to truthound.datasources.base.DataSourceConfig.
 */
export interface DataSourceConfig {
  /** Data source name */
  name?: string
  /** Maximum rows before requiring sampling */
  max_rows?: number
  /** Memory limit in MB */
  max_memory_mb?: number
  /** Default sample size for sampling */
  sample_size?: number
  /** Seed for reproducible sampling */
  sample_seed?: number
  /** Cache schema information */
  cache_schema?: boolean
  /** Enable strict type checking */
  strict_types?: boolean
  /** Custom metadata */
  metadata?: Record<string, unknown>
}

/**
 * Configuration for file-based sources.
 * Maps to truthound.datasources.polars_source.FileDataSourceConfig.
 */
export interface FileDataSourceConfig extends DataSourceConfig {
  /** File path */
  path: string
  /** Rows to read for schema inference */
  infer_schema_length?: number
  /** Maximum rows to read */
  n_rows?: number
  /** File encoding */
  encoding?: string
  /** Ignore parsing errors */
  ignore_errors?: boolean
  /** CSV separator character */
  separator?: string
}

/**
 * Configuration for SQL data sources.
 * Maps to truthound.datasources.sql.base.SQLDataSourceConfig.
 */
export interface SQLDataSourceConfig extends DataSourceConfig {
  /** Connection pool size */
  pool_size?: number
  /** Pool acquire timeout in seconds */
  pool_timeout?: number
  /** Query timeout in seconds */
  query_timeout?: number
  /** Rows to fetch per batch */
  fetch_size?: number
  /** Use server-side cursors */
  use_server_side_cursor?: boolean
  /** Database schema name */
  schema_name?: string
}

/**
 * PostgreSQL specific configuration.
 */
export interface PostgreSQLConfig extends SQLDataSourceConfig {
  host: string
  port?: number
  database: string
  user?: string
  password?: string
  /** SSL mode: disable, require, verify-ca, verify-full */
  sslmode?: 'disable' | 'prefer' | 'require' | 'verify-ca' | 'verify-full'
  /** Application name for connection identification */
  application_name?: string
  /** Table or query */
  table?: string
  query?: string
}

/**
 * MySQL specific configuration.
 */
export interface MySQLConfig extends SQLDataSourceConfig {
  host: string
  port?: number
  database: string
  user?: string
  password?: string
  /** Character set */
  charset?: string
  /** SSL configuration */
  ssl?: Record<string, unknown>
  /** Auto-commit mode */
  autocommit?: boolean
  /** Table or query */
  table?: string
  query?: string
}

/**
 * SQLite specific configuration.
 */
export interface SQLiteConfig extends DataSourceConfig {
  /** Database file path or :memory: */
  database: string
  /** Connection timeout */
  timeout?: number
  /** Table or query */
  table?: string
  query?: string
}

/**
 * BigQuery specific configuration.
 */
export interface BigQueryConfig extends SQLDataSourceConfig {
  /** GCP project ID */
  project: string
  /** BigQuery dataset */
  dataset: string
  /** Data location */
  location?: string
  /** Use legacy SQL syntax */
  use_legacy_sql?: boolean
  /** Cost control limit in bytes */
  maximum_bytes_billed?: number
  /** Job timeout in seconds */
  job_timeout?: number
  /** Path to credentials JSON file */
  credentials_path?: string
  /** Table or query */
  table?: string
  query?: string
}

/**
 * Snowflake specific configuration.
 */
export interface SnowflakeConfig extends SQLDataSourceConfig {
  /** Snowflake account identifier */
  account: string
  user: string
  password?: string
  database: string
  /** Compute warehouse */
  warehouse?: string
  /** Role to use */
  role?: string
  /** Authentication method */
  authenticator?: 'snowflake' | 'externalbrowser' | 'oauth'
  /** Private key file path for key-pair auth */
  private_key_path?: string
  private_key_passphrase?: string
  /** OAuth token */
  token?: string
  /** Keep session alive */
  client_session_keep_alive?: boolean
  /** Table or query */
  table?: string
  query?: string
}

/**
 * Redshift specific configuration.
 */
export interface RedshiftConfig extends SQLDataSourceConfig {
  host: string
  port?: number
  database: string
  user?: string
  password?: string
  /** Use IAM authentication */
  iam_auth?: boolean
  /** Cluster identifier for IAM auth */
  cluster_identifier?: string
  /** Database user for IAM auth */
  db_user?: string
  /** AWS credentials */
  access_key_id?: string
  secret_access_key?: string
  session_token?: string
  /** SSL settings */
  ssl?: boolean
  ssl_mode?: 'verify-ca' | 'verify-full'
  /** Table or query */
  table?: string
  query?: string
}

/**
 * Databricks specific configuration.
 */
export interface DatabricksConfig extends SQLDataSourceConfig {
  /** Databricks workspace hostname */
  host: string
  /** SQL warehouse HTTP path */
  http_path: string
  /** Personal access token */
  access_token?: string
  /** Unity Catalog name */
  catalog?: string
  /** Use cloud fetch optimization */
  use_cloud_fetch?: boolean
  /** Maximum download threads */
  max_download_threads?: number
  /** OAuth client ID */
  client_id?: string
  /** OAuth client secret */
  client_secret?: string
  /** Use OAuth authentication */
  use_oauth?: boolean
  /** Table or query */
  table?: string
  query?: string
}

/**
 * Oracle specific configuration.
 */
export interface OracleConfig extends SQLDataSourceConfig {
  host: string
  port?: number
  /** Service name */
  service_name?: string
  /** SID (alternative to service_name) */
  sid?: string
  user?: string
  password?: string
  /** Table or query */
  table?: string
  query?: string
}

/**
 * SQL Server specific configuration.
 */
export interface SQLServerConfig extends SQLDataSourceConfig {
  host: string
  port?: number
  database: string
  user?: string
  password?: string
  /** Use Windows authentication */
  trusted_connection?: boolean
  /** ODBC driver name */
  driver?: string
  /** Table or query */
  table?: string
  query?: string
}

/**
 * MongoDB specific configuration (async).
 */
export interface MongoDBConfig extends DataSourceConfig {
  /** MongoDB connection string */
  connection_string: string
  database: string
  collection: string
  /** Query filter */
  filter?: Record<string, unknown>
  /** Field projection */
  projection?: Record<string, unknown>
}

/**
 * Elasticsearch specific configuration (async).
 */
export interface ElasticsearchConfig extends DataSourceConfig {
  /** Elasticsearch hosts */
  hosts: string[]
  /** Index name or pattern */
  index: string
  /** Search query */
  query?: Record<string, unknown>
  /** Scroll timeout */
  scroll_timeout?: string
}

/**
 * Kafka specific configuration (async).
 */
export interface KafkaConfig extends DataSourceConfig {
  /** Kafka bootstrap servers */
  bootstrap_servers: string
  /** Topic name */
  topic: string
  /** Consumer group ID */
  group_id?: string
  /** Auto offset reset: earliest, latest */
  auto_offset_reset?: 'earliest' | 'latest'
  /** Maximum poll records */
  max_poll_records?: number
}

/**
 * Spark specific configuration.
 */
export interface SparkConfig extends DataSourceConfig {
  /** Maximum rows for local processing */
  max_rows_for_local?: number
  /** Sampling fraction (0-1) */
  sampling_fraction?: number
  /** Persist sampled data */
  persist_sampled?: boolean
  /** Force sampling even for small datasets */
  force_sampling?: boolean
  /** Repartition count for sampling */
  repartition_for_sampling?: number
}

/**
 * Union type for all source configs.
 */
export type AnySourceConfig =
  | DataSourceConfig
  | FileDataSourceConfig
  | SQLDataSourceConfig
  | PostgreSQLConfig
  | MySQLConfig
  | SQLiteConfig
  | BigQueryConfig
  | SnowflakeConfig
  | RedshiftConfig
  | DatabricksConfig
  | OracleConfig
  | SQLServerConfig
  | MongoDBConfig
  | ElasticsearchConfig
  | KafkaConfig
  | SparkConfig

// ============================================================================
// Source Type Definitions
// ============================================================================

/**
 * Field types for dynamic form rendering.
 */
export type FieldType =
  | 'text'
  | 'password'
  | 'number'
  | 'select'
  | 'boolean'
  | 'file_path'
  | 'textarea'
  | 'json'
  | 'url'

/**
 * Option for select fields.
 */
export interface FieldOption {
  value: string
  label: string
  description?: string
}

/**
 * Definition of a configuration field for dynamic form rendering.
 */
export interface FieldDefinition {
  /** Field name (key in config object) */
  name: string
  /** Display label */
  label: string
  /** Field type for rendering */
  type: FieldType
  /** Whether field is required */
  required: boolean
  /** Placeholder text */
  placeholder?: string
  /** Help text / description */
  description?: string
  /** Default value */
  default?: unknown
  /** Options for select fields */
  options?: FieldOption[]
  /** Minimum value for number fields */
  min_value?: number
  /** Maximum value for number fields */
  max_value?: number
  /** Field this depends on (conditional visibility) */
  depends_on?: string
  /** Value that dependency field must have */
  depends_value?: unknown
  /** Whether to show in advanced section */
  advanced?: boolean
  /** Validation pattern (regex) */
  pattern?: string
  /** Pattern validation error message */
  pattern_message?: string
}

/**
 * Complete definition of a source type for UI rendering.
 */
export interface SourceTypeDefinition {
  /** Source type identifier */
  type: SourceType
  /** Display name */
  name: string
  /** Description */
  description: string
  /** Icon name (lucide icon) */
  icon: string
  /** Category for grouping */
  category: SourceCategory
  /** Configuration fields */
  fields: FieldDefinition[]
  /** Required field names */
  required_fields: string[]
  /** Optional field names */
  optional_fields: string[]
  /** Link to documentation */
  docs_url?: string
  /** Capabilities supported by this source type */
  capabilities: DataSourceCapability[]
  /** Required Python package */
  required_package?: string
  /** Whether source requires async operations */
  is_async: boolean
  /** Connection string example */
  connection_string_example?: string
  /** Whether source supports table mode */
  supports_table: boolean
  /** Whether source supports query mode */
  supports_query: boolean
}

/**
 * Category definition for grouping source types.
 */
export interface SourceCategoryDefinition {
  id: SourceCategory
  name: string
  description: string
  icon: string
}

// ============================================================================
// Data Source Instance Types
// ============================================================================

/**
 * Schema information for a column.
 */
export interface ColumnSchema {
  name: string
  type: ColumnType
  nullable: boolean
  description?: string
  /** Statistics from profiling */
  stats?: ColumnStats
}

/**
 * Statistics for a column.
 */
export interface ColumnStats {
  null_count?: number
  null_percentage?: number
  distinct_count?: number
  min_value?: unknown
  max_value?: unknown
  mean?: number
  std_dev?: number
  /** Sample values */
  sample_values?: unknown[]
}

/**
 * Registered data source in the dashboard.
 */
export interface DataSource {
  id: string
  name: string
  description?: string
  type: SourceType
  /** Connection configuration (stored encrypted) */
  config: Record<string, unknown>
  /** Detected capabilities */
  capabilities: DataSourceCapability[]
  /** Schema information */
  schema?: Record<string, ColumnType>
  /** Column details */
  columns?: ColumnSchema[]
  /** Row count if known */
  row_count?: number
  /** Whether source requires async */
  is_async: boolean
  /** Last connection test result */
  last_test?: ConnectionTestResult
  /** Tags for organization */
  tags?: string[]
  /** Creation timestamp */
  created_at: string
  /** Last updated timestamp */
  updated_at: string
}

/**
 * Result of a connection test.
 */
export interface ConnectionTestResult {
  success: boolean
  message?: string
  error?: string
  /** Test duration in milliseconds */
  latency_ms?: number
  /** Additional metadata */
  metadata?: ConnectionTestMetadata
  /** Timestamp of test */
  tested_at: string
}

/**
 * Metadata from connection test.
 */
export interface ConnectionTestMetadata {
  row_count?: number
  column_count?: number
  server_version?: string
  capabilities?: DataSourceCapability[]
  schema?: Record<string, ColumnType>
  /** Server information */
  server_info?: Record<string, unknown>
  /** Whether sampling was used */
  sampled?: boolean
  /** Sample size if sampled */
  sample_size?: number
}

// ============================================================================
// API Request/Response Types
// ============================================================================

/**
 * Request to create a new data source.
 */
export interface CreateSourceRequest {
  name: string
  description?: string
  type: SourceType
  config: Record<string, unknown>
  tags?: string[]
}

/**
 * Request to update a data source.
 */
export interface UpdateSourceRequest {
  name?: string
  description?: string
  config?: Record<string, unknown>
  tags?: string[]
}

/**
 * Request to test a connection.
 */
export interface TestConnectionRequest {
  type: SourceType
  config: Record<string, unknown>
}

/**
 * Response from connection test.
 */
export interface TestConnectionResponse extends ConnectionTestResult {
  /** Suggested configuration adjustments */
  suggestions?: ConfigSuggestion[]
}

/**
 * Suggestion for configuration improvement.
 */
export interface ConfigSuggestion {
  field: string
  current_value?: unknown
  suggested_value: unknown
  reason: string
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Get category for a source type.
 */
export function getSourceCategory(type: SourceType): SourceCategory {
  const categoryMap: Record<SourceType, SourceCategory> = {
    file: 'file',
    csv: 'file',
    parquet: 'file',
    json: 'file',
    ndjson: 'file',
    jsonl: 'file',
    polars: 'dataframe',
    pandas: 'dataframe',
    sqlite: 'database',
    postgresql: 'database',
    mysql: 'database',
    bigquery: 'warehouse',
    snowflake: 'warehouse',
    redshift: 'warehouse',
    databricks: 'warehouse',
    oracle: 'enterprise',
    sqlserver: 'enterprise',
    mongodb: 'nosql',
    elasticsearch: 'nosql',
    kafka: 'streaming',
    kinesis: 'streaming',
    spark: 'bigdata',
  }
  return categoryMap[type] || 'file'
}

/**
 * Check if source type is file-based.
 */
export function isFileSourceType(type: SourceType | string): boolean {
  return ['file', 'csv', 'parquet', 'json', 'ndjson', 'jsonl'].includes(type.toLowerCase())
}

/**
 * Check if source type is SQL-based.
 */
export function isSQLSourceType(type: SourceType | string): boolean {
  return [
    'sqlite', 'postgresql', 'mysql',
    'bigquery', 'snowflake', 'redshift', 'databricks',
    'oracle', 'sqlserver',
  ].includes(type.toLowerCase())
}

/**
 * Check if source type requires async operations.
 */
export function isAsyncSourceType(type: SourceType | string): boolean {
  return ['mongodb', 'elasticsearch', 'kafka', 'kinesis'].includes(type.toLowerCase())
}

/**
 * Check if source type is a cloud data warehouse.
 */
export function isCloudWarehouseType(type: SourceType | string): boolean {
  return ['bigquery', 'snowflake', 'redshift', 'databricks'].includes(type.toLowerCase())
}

/**
 * Get default capabilities for a source type.
 */
export function getDefaultCapabilities(type: SourceType | string): DataSourceCapability[] {
  const lower = type.toLowerCase()

  // File sources
  if (['csv', 'ndjson', 'jsonl', 'file'].includes(lower)) {
    return ['lazy_evaluation', 'sampling', 'schema_inference']
  }
  if (lower === 'parquet') {
    return ['lazy_evaluation', 'sampling', 'schema_inference', 'row_count']
  }
  if (lower === 'json') {
    return ['schema_inference']
  }

  // SQL databases
  if (isSQLSourceType(lower)) {
    return ['sql_pushdown', 'sampling', 'schema_inference', 'row_count']
  }

  // NoSQL
  if (['mongodb', 'elasticsearch'].includes(lower)) {
    return ['sampling', 'schema_inference', 'streaming']
  }

  // Streaming
  if (['kafka', 'kinesis'].includes(lower)) {
    return ['streaming', 'sampling']
  }

  // Spark
  if (lower === 'spark') {
    return ['lazy_evaluation', 'sampling', 'schema_inference']
  }

  return ['schema_inference']
}

/**
 * Human-readable labels for capabilities.
 */
export const CAPABILITY_INFO: Record<
  DataSourceCapability,
  { label: string; description: string; icon: string }
> = {
  lazy_evaluation: {
    label: 'Lazy Evaluation',
    description: 'Supports deferred execution for memory-efficient processing of large datasets',
    icon: 'Zap',
  },
  sql_pushdown: {
    label: 'SQL Pushdown',
    description: 'Can push validation operations to the database server for better performance',
    icon: 'Filter',
  },
  sampling: {
    label: 'Efficient Sampling',
    description: 'Supports efficient random sampling for validating large datasets',
    icon: 'Shuffle',
  },
  streaming: {
    label: 'Streaming',
    description: 'Supports streaming/chunked reads for real-time data processing',
    icon: 'Radio',
  },
  schema_inference: {
    label: 'Schema Inference',
    description: 'Can automatically detect column types without scanning entire dataset',
    icon: 'FileSearch',
  },
  row_count: {
    label: 'Fast Row Count',
    description: 'Can efficiently get row count without full table scan',
    icon: 'Hash',
  },
}

/**
 * Category information for UI.
 */
export const CATEGORY_INFO: Record<
  SourceCategory,
  { name: string; description: string; icon: string }
> = {
  file: {
    name: 'File Sources',
    description: 'Local and remote file formats',
    icon: 'File',
  },
  dataframe: {
    name: 'DataFrames',
    description: 'In-memory data structures',
    icon: 'Table2',
  },
  database: {
    name: 'SQL Databases',
    description: 'Traditional relational databases',
    icon: 'Database',
  },
  warehouse: {
    name: 'Cloud Warehouses',
    description: 'Cloud-native data warehouses',
    icon: 'Cloud',
  },
  enterprise: {
    name: 'Enterprise',
    description: 'Enterprise database systems',
    icon: 'Building2',
  },
  nosql: {
    name: 'NoSQL',
    description: 'Document and search databases',
    icon: 'Layers',
  },
  streaming: {
    name: 'Streaming',
    description: 'Real-time streaming platforms',
    icon: 'Radio',
  },
  bigdata: {
    name: 'Big Data',
    description: 'Distributed processing frameworks',
    icon: 'Cpu',
  },
}

/**
 * Required packages for source types.
 */
export const SOURCE_PACKAGES: Partial<Record<SourceType, string>> = {
  pandas: 'pip install truthound[pandas]',
  spark: 'pip install truthound[spark]',
  postgresql: 'pip install truthound[postgresql]',
  mysql: 'pip install truthound[mysql]',
  bigquery: 'pip install truthound[bigquery]',
  snowflake: 'pip install truthound[snowflake]',
  redshift: 'pip install truthound[redshift]',
  databricks: 'pip install truthound[databricks]',
  oracle: 'pip install truthound[oracle]',
  sqlserver: 'pip install truthound[sqlserver]',
  mongodb: 'pip install truthound[mongodb]',
  elasticsearch: 'pip install truthound[elasticsearch]',
  kafka: 'pip install truthound[kafka]',
  kinesis: 'pip install truthound[kinesis]',
}
