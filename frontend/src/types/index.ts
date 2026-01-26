/**
 * Type exports for truthound-dashboard frontend.
 *
 * Organized by domain:
 * - DataSources: Types for data source connections (SQL, NoSQL, Files, etc.)
 * - Validators: Validation rules and configurations
 * - Reporters: Report generation and formats
 */

// =============================================================================
// DataSources
// =============================================================================

export type {
  // Source types
  SourceType,
  SourceCategory,
  DataSourceCapability,
  ColumnType,

  // Configuration types
  DataSourceConfig,
  FileDataSourceConfig,
  SQLDataSourceConfig,
  PostgreSQLConfig,
  MySQLConfig,
  SQLiteConfig,
  BigQueryConfig,
  SnowflakeConfig,
  RedshiftConfig,
  DatabricksConfig,
  OracleConfig,
  SQLServerConfig,
  MongoDBConfig,
  ElasticsearchConfig,
  KafkaConfig,
  SparkConfig,
  AnySourceConfig,

  // Field definitions
  FieldType,
  FieldOption,
  FieldDefinition,
  SourceTypeDefinition,
  SourceCategoryDefinition,

  // Data source instances
  ColumnSchema,
  ColumnStats,
  DataSource,
  ConnectionTestResult,
  ConnectionTestMetadata,

  // API types
  CreateSourceRequest,
  UpdateSourceRequest,
  TestConnectionRequest,
  TestConnectionResponse,
  ConfigSuggestion,
} from './datasources'

export {
  // Helper functions
  getSourceCategory,
  isFileSourceType,
  isSQLSourceType,
  isAsyncSourceType,
  isCloudWarehouseType,
  getDefaultCapabilities,

  // Constants
  CAPABILITY_INFO,
  CATEGORY_INFO,
  SOURCE_PACKAGES,
} from './datasources'

// =============================================================================
// Validators
// =============================================================================

export * from './validators'

// =============================================================================
// Reporters
// =============================================================================

export type {
  // Format types
  ReportFormatType,
  ReportThemeType,
  ReportStatus,
  ReportLocale,
  CIPlatformType,

  // Info types
  ReportFormatInfo,
  ReportThemeInfo,
  LocaleInfo,
  CIPlatformInfo,

  // Configuration
  ReporterConfig,

  // Issue types
  ReportIssueSeverity,
  ValidationIssueData,
  ValidationSummary,
  DataStatistics,
  ReportData,
  ReportOutput,

  // Generated reports
  GeneratedReport,
  ReportCreateOptions,
  ReportUpdateOptions,
  ReportStatistics,

  // Custom reporters
  ReporterOutputFormat,
  CustomReporter,
  CustomReporterCreateOptions,
  ReporterMixin,
  SDKReporter,
  ReporterBuilderOptions,

  // API types
  AvailableFormatsResponse,
  ReportListResponse,
  BulkReportRequest,
  BulkReportResponse,
  GenerateReportRequest,
  GenerateReportResponse,
  ReporterPreviewRequest,
  ReporterPreviewResponse,

  // ValidationResult types (for full reporter functionality)
  ResultStatus,
  IssueSeverity,
  ValidatorResult,
  ResultStatistics,
  ValidationResult,
} from './reporters'

export {
  // Constants
  REPORT_FORMATS,
  REPORT_THEMES,
  REPORT_LOCALES,
  CI_PLATFORMS,
  DEFAULT_REPORTER_CONFIG,

  // Helper functions
  getFormatInfo,
  getThemeInfo,
  getLocaleInfo,
  getCIPlatformInfo,
  formatSupportsTheme,
  formatSupportsI18n,
  getFormatExtension,
  getFormatContentType,
  createDefaultConfig,
  formatFileSize,
  formatGenerationTime,
  isReportDownloadable,
  isReportExpired,
  getStatusVariant,
} from './reporters'

// =============================================================================
// Checkpoint (Validation Pipeline Orchestration)
// =============================================================================

export type {
  // Status and configuration
  CheckpointStatus,
  CheckpointConfig,
  CheckpointResult,
  ValidationIssue,
  IssueSeverity as CheckpointIssueSeverity,
  Checkpoint,
  RouterConfig,
  CheckpointStatistics,
  CheckpointRunSummary,
  // API types
  CreateCheckpointRequest,
  UpdateCheckpointRequest,
  RunCheckpointRequest,
  RunCheckpointResponse,
  ListCheckpointsResponse,
  ListCheckpointRunsResponse,
  ListCheckpointsParams,
  ListCheckpointRunsParams,
} from './checkpoint'

export {
  // Constants
  CHECKPOINT_STATUS_LABELS,
  CHECKPOINT_STATUS_VARIANTS,
  DEFAULT_CHECKPOINT_CONFIG,
  SEVERITY_ORDER,
  // Helper functions
  isCheckpointSuccess,
  isCheckpointFailed,
  isCheckpointTerminal,
  getStatusBadgeVariant,
  calculatePassRate,
  formatDuration,
  sortIssuesBySeverity,
} from './checkpoint'

// =============================================================================
// Actions (Checkpoint Post-Validation Actions)
// =============================================================================

export type {
  // Status and types
  ActionStatus,
  NotifyCondition,
  ActionType,
  ActionCategory,
  ActionTypeInfo,
  ActionConfigField,
  ActionConfigSchema,
  // Configuration types
  ActionConfigBase,
  SlackActionConfig,
  EmailActionConfig,
  TeamsActionConfig,
  DiscordActionConfig,
  TelegramActionConfig,
  PagerDutyActionConfig,
  OpsGenieActionConfig,
  WebhookActionConfig,
  FileStorageActionConfig,
  S3StorageActionConfig,
  GCSStorageActionConfig,
  UpdateDocsActionConfig,
  CustomActionConfig,
  ShellCommandActionConfig,
  ActionConfig,
  // Result types
  ActionResult,
} from './actions'

export {
  // Constants
  NOTIFY_CONDITION_LABELS,
  ACTION_TYPE_INFO,
  // Helper functions
  getActionTypeInfo,
  getActionsByCategory,
  createDefaultActionConfig,
  isActionSuccess,
  isActionFailed,
  isActionSkipped,
} from './actions'

// =============================================================================
// Routing (Conditional Action Execution)
// =============================================================================

export type {
  // Mode and priority
  RouteMode,
  RoutePriority,
  // Rule types
  RoutingRuleType,
  RuleTypeInfo,
  // Rule configurations
  BaseRuleConfig,
  AlwaysRuleConfig,
  NeverRuleConfig,
  StatusRuleConfig,
  SeverityRuleConfig,
  IssueCountRuleConfig,
  PassRateRuleConfig,
  TagRuleConfig,
  DataAssetRuleConfig,
  MetadataRuleConfig,
  TimeWindowRuleConfig,
  ErrorRuleConfig,
  AllOfRuleConfig,
  AnyOfRuleConfig,
  NotRuleConfig,
  Jinja2RuleConfig,
  PythonRuleConfig,
  RoutingRule,
  // Route and router
  Route,
  Router,
  RouteContext,
} from './routing'

export {
  // Constants
  ROUTE_MODE_LABELS,
  ROUTE_MODE_DESCRIPTIONS,
  ROUTE_PRIORITY_VALUES,
  ROUTE_PRIORITY_LABELS,
  RULE_TYPE_INFO,
  // Helper functions
  getRuleTypeInfo,
  getRulesByCategory,
  createDefaultRuleConfig,
  describeRule,
  validateRoute,
} from './routing'

// =============================================================================
// Triggers (Checkpoint Execution Scheduling)
// =============================================================================

export type {
  // Types and status
  TriggerType,
  TriggerTypeInfo,
  TriggerStatus,
  // Configuration types
  TriggerConfigBase,
  CronTriggerConfig,
  IntervalTriggerConfig,
  EventTriggerConfig,
  FileWatchTriggerConfig,
  DataChangeTriggerConfig,
  WebhookTriggerConfig,
  ManualTriggerConfig,
  OneTimeTriggerConfig,
  PipelineTriggerConfig,
  TriggerConfig,
  // Instance and result
  Trigger,
  TriggerResult,
} from './triggers'

export {
  // Constants
  TRIGGER_TYPE_INFO,
  TRIGGER_STATUS_LABELS,
  COMMON_CRON_EXPRESSIONS,
  // Helper functions
  getTriggerTypeInfo,
  createDefaultTriggerConfig,
  validateTriggerConfig,
  describeCronExpression,
  getNextCronRun,
} from './triggers'

// =============================================================================
// Throttling (Action Rate Limiting)
// =============================================================================

export type {
  // Algorithm and behavior
  ThrottlingAlgorithm,
  ThrottlingAlgorithmInfo,
  ThrottleBehavior,
  // Time window
  WindowUnit,
  TimeWindow,
  // Configuration
  ThrottlingConfig,
  ActionThrottleConfig,
  // Statistics and result
  ThrottlingStats,
  ThrottleResult,
} from './throttling'

export {
  // Constants
  THROTTLING_ALGORITHM_INFO,
  THROTTLE_BEHAVIOR_LABELS,
  COMMON_TIME_WINDOWS,
  DEFAULT_THROTTLING_CONFIG,
  ACTION_THROTTLE_PRESETS,
  // Helper functions
  timeWindowToSeconds,
  formatTimeWindow,
  validateThrottlingConfig,
  calculateRatePerSecond,
  formatRateLimit,
  createThrottlingConfigFromPreset,
} from './throttling'

// =============================================================================
// Deduplication (Duplicate Notification Prevention)
// =============================================================================

export type {
  // Policy and strategy
  DeduplicationPolicy,
  DeduplicationPolicyInfo,
  WindowStrategyType,
  WindowStrategyInfo,
  // Fingerprint
  NotificationFingerprint,
  FingerprintOptions,
  // Configuration
  DeduplicationConfig,
  DeduplicationStoreConfig,
  // Result and statistics
  DeduplicationResult,
  DeduplicationStats,
} from './deduplication'

export {
  // Constants
  DEDUPLICATION_POLICY_INFO,
  WINDOW_STRATEGY_INFO,
  DEFAULT_DEDUPLICATION_CONFIG,
  DEDUPLICATION_PRESETS,
  // Helper functions
  validateDeduplicationConfig,
  getEffectiveWindow,
  generateSimpleFingerprint,
  formatSuppressionCount,
  createDeduplicationConfigFromPreset,
} from './deduplication'

// =============================================================================
// Escalation (Multi-Level Alert Escalation)
// =============================================================================

export type {
  // State and types
  EscalationState,
  EscalationStateInfo,
  TargetType,
  TargetTypeInfo,
  EscalationTrigger,
  // Target and level
  EscalationTarget,
  EscalationLevel,
  // Policy and record
  EscalationPolicy,
  EscalationRecord,
  EscalationEvent,
  // Statistics
  EscalationStats,
  // API types
  CreateEscalationPolicyRequest,
  TriggerEscalationRequest,
  AcknowledgeEscalationRequest,
  ResolveEscalationRequest,
} from './escalation'

export {
  // Constants
  ESCALATION_STATE_INFO,
  TARGET_TYPE_INFO,
  ESCALATION_TRIGGER_INFO,
  DEFAULT_ESCALATION_POLICY,
  // Helper functions
  isEscalationTerminal,
  isEscalationActive,
  getMaxLevel,
  getLevel,
  getNextLevel,
  calculateTotalEscalationTime,
  formatEscalationDuration,
  validateEscalationPolicy,
  createDefaultEscalationLevel,
  createTarget,
} from './escalation'

// =============================================================================
// Utilities (Common Types and Functions)
// =============================================================================

export type {
  // Generic utility types
  PartialBy,
  RequiredBy,
  DeepReadonly,
  DeepPartial,
  KeysOfType,
  ValueOf,
  ArrayElement,
  Brand,

  // Branded ID types
  SourceId,
  CheckpointId,
  ValidationId,
  ReportId,
  UserId,

  // Result types
  Success,
  Failure,
  Result,
  AsyncResult,

  // Pagination types
  PaginationParams,
  PaginatedResponse,

  // Status types
  EntityStatus,
  OperationStatus,
  Severity,

  // Validation types
  ValidationError,
  ValidationResult as UtilValidationResult,

  // Factory types
  Factory,
} from './utils'

export {
  // Result functions
  success,
  failure,
  isSuccess,
  isFailure,
  unwrap,
  unwrapOr,
  tryCatch,

  // Pagination
  createPaginatedResponse,

  // Severity utilities
  SEVERITY_ORDER as UTIL_SEVERITY_ORDER,
  compareSeverity,
  isSeverityAtOrAbove,

  // Type guards
  isDefined,
  isString,
  isNumber,
  isBoolean,
  isArray,
  isPlainObject,
  isFunction,
  isValidDate,
  isISODateString,

  // Transformation utilities
  snakeToCamel,
  camelToSnake,
  transformKeysToCamel,
  transformKeysToSnake,

  // Validation utilities
  createValidationError,
  validResult,
  invalidResult,
  combineValidationResults,

  // Factory utilities
  FactoryRegistry,

  // Memoization
  memoize,
  memoizeWithKey,

  // Date utilities
  toISOString,
  fromISOString,
  formatDuration as formatDurationMs,
  relativeTime,

  // String utilities
  truncate,
  capitalize,
  titleCase,
  formatBytes,

  // Object utilities
  deepClone,
  deepMerge,
  pick,
  omit,
  filterObject,
} from './utils'
