/**
 * Action types for checkpoint-based validation pipelines.
 *
 * Actions are executed after validation completes. They can store results,
 * send notifications, or integrate with external systems.
 *
 * Supported action types:
 * - Storage: Store validation results to filesystem, S3, GCS
 * - Notifications: Slack, Email, Teams, Discord, Telegram, PagerDuty, OpsGenie
 * - Webhook: Call any HTTP endpoint
 * - Custom: Execute Python callbacks or shell commands
 * - DataDocs: Generate HTML/Markdown documentation
 */

// =============================================================================
// Action Status and Conditions
// =============================================================================

/**
 * Status of an action execution.
 */
export type ActionStatus =
  | 'pending'      // Not yet started
  | 'running'      // Currently executing
  | 'success'      // Completed successfully
  | 'failure'      // Failed
  | 'skipped'      // Skipped due to notify_on condition
  | 'compensated'  // Rolled back (for transactional actions)

/**
 * Conditions under which actions are triggered.
 */
export type NotifyCondition =
  | 'always'           // Every run
  | 'success'          // Validation passed
  | 'failure'          // Validation failed
  | 'error'            // System error occurred
  | 'failure_or_error' // Failure or error
  | 'not_success'      // Any non-success status
  | 'warning'          // Warning status

/**
 * Human-readable labels for notify conditions.
 */
export const NOTIFY_CONDITION_LABELS: Record<NotifyCondition, string> = {
  always: 'Always',
  success: 'On Success',
  failure: 'On Failure',
  error: 'On Error',
  failure_or_error: 'On Failure or Error',
  not_success: 'Not Success',
  warning: 'On Warning',
}

// =============================================================================
// Action Types
// =============================================================================

/**
 * Available action types.
 */
export type ActionType =
  | 'slack'
  | 'email'
  | 'teams'
  | 'discord'
  | 'telegram'
  | 'pagerduty'
  | 'opsgenie'
  | 'webhook'
  | 'store_result'
  | 'update_docs'
  | 'custom'
  | 'callback'
  | 'shell_command'
  | 'file_storage'
  | 's3_storage'
  | 'gcs_storage'

/**
 * Action type categories.
 */
export type ActionCategory = 'notification' | 'storage' | 'integration' | 'custom'

/**
 * Action type metadata.
 */
export interface ActionTypeInfo {
  type: ActionType
  label: string
  description: string
  category: ActionCategory
  icon?: string
  configSchema?: ActionConfigSchema
}

/**
 * Action config field schema.
 */
export interface ActionConfigField {
  name: string
  type: 'string' | 'number' | 'boolean' | 'select' | 'array' | 'object'
  label: string
  description?: string
  required?: boolean
  default?: unknown
  options?: { value: string; label: string }[]
  validation?: {
    min?: number
    max?: number
    pattern?: string
    message?: string
  }
}

/**
 * Schema for action configuration.
 */
export interface ActionConfigSchema {
  fields: ActionConfigField[]
}

/**
 * Metadata for all action types.
 */
export const ACTION_TYPE_INFO: Record<ActionType, ActionTypeInfo> = {
  slack: {
    type: 'slack',
    label: 'Slack',
    description: 'Send notifications via Slack webhook',
    category: 'notification',
    icon: 'slack',
  },
  email: {
    type: 'email',
    label: 'Email',
    description: 'Send email notifications',
    category: 'notification',
    icon: 'mail',
  },
  teams: {
    type: 'teams',
    label: 'Microsoft Teams',
    description: 'Send notifications via Teams webhook',
    category: 'notification',
    icon: 'users',
  },
  discord: {
    type: 'discord',
    label: 'Discord',
    description: 'Send notifications via Discord webhook',
    category: 'notification',
    icon: 'message-circle',
  },
  telegram: {
    type: 'telegram',
    label: 'Telegram',
    description: 'Send notifications via Telegram bot',
    category: 'notification',
    icon: 'send',
  },
  pagerduty: {
    type: 'pagerduty',
    label: 'PagerDuty',
    description: 'Create PagerDuty incidents',
    category: 'notification',
    icon: 'alert-triangle',
  },
  opsgenie: {
    type: 'opsgenie',
    label: 'OpsGenie',
    description: 'Create OpsGenie alerts',
    category: 'notification',
    icon: 'bell',
  },
  webhook: {
    type: 'webhook',
    label: 'Webhook',
    description: 'Call any HTTP endpoint',
    category: 'integration',
    icon: 'globe',
  },
  store_result: {
    type: 'store_result',
    label: 'Store Result',
    description: 'Store validation results to storage',
    category: 'storage',
    icon: 'database',
  },
  update_docs: {
    type: 'update_docs',
    label: 'Update DataDocs',
    description: 'Generate HTML/Markdown documentation',
    category: 'storage',
    icon: 'file-text',
  },
  custom: {
    type: 'custom',
    label: 'Custom',
    description: 'Execute custom Python code',
    category: 'custom',
    icon: 'code',
  },
  callback: {
    type: 'callback',
    label: 'Callback',
    description: 'Execute a Python callback function',
    category: 'custom',
    icon: 'terminal',
  },
  shell_command: {
    type: 'shell_command',
    label: 'Shell Command',
    description: 'Execute a shell command',
    category: 'custom',
    icon: 'terminal',
  },
  file_storage: {
    type: 'file_storage',
    label: 'File Storage',
    description: 'Store results to local filesystem',
    category: 'storage',
    icon: 'folder',
  },
  s3_storage: {
    type: 's3_storage',
    label: 'S3 Storage',
    description: 'Store results to Amazon S3',
    category: 'storage',
    icon: 'cloud',
  },
  gcs_storage: {
    type: 'gcs_storage',
    label: 'GCS Storage',
    description: 'Store results to Google Cloud Storage',
    category: 'storage',
    icon: 'cloud',
  },
}

// =============================================================================
// Action Configuration
// =============================================================================

/**
 * Base configuration for all actions.
 */
export interface ActionConfigBase {
  /** Action name for identification */
  name: string
  /** Action type */
  type: ActionType
  /** When to execute this action */
  notify_on: NotifyCondition
  /** Whether this action is enabled */
  enabled: boolean
  /** Maximum execution time in seconds */
  timeout_seconds?: number
  /** Number of retries on failure */
  retry_count?: number
  /** Delay between retries in seconds */
  retry_delay_seconds?: number
  /** Fail checkpoint on action error */
  fail_checkpoint_on_error?: boolean
  /** Additional metadata */
  metadata?: Record<string, unknown>
}

/**
 * Slack notification configuration.
 */
export interface SlackActionConfig extends ActionConfigBase {
  type: 'slack'
  /** Slack webhook URL */
  webhook_url: string
  /** Channel override */
  channel?: string
  /** Bot display name */
  username?: string
  /** Bot icon emoji */
  icon_emoji?: string
  /** Include detailed statistics */
  include_details?: boolean
  /** User IDs to mention on failure */
  mention_on_failure?: string[]
  /** Custom message template */
  custom_message?: string
}

/**
 * Email notification configuration.
 */
export interface EmailActionConfig extends ActionConfigBase {
  type: 'email'
  /** SMTP server host */
  smtp_host: string
  /** SMTP server port */
  smtp_port: number
  /** SMTP authentication user */
  smtp_user?: string
  /** SMTP authentication password (env var reference) */
  smtp_password?: string
  /** Use TLS */
  use_tls?: boolean
  /** Use SSL */
  use_ssl?: boolean
  /** Sender address */
  from_address: string
  /** Recipient addresses */
  to_addresses: string[]
  /** CC addresses */
  cc_addresses?: string[]
  /** Subject template */
  subject_template?: string
  /** Include HTML body */
  include_html?: boolean
  /** Provider: smtp, sendgrid, ses */
  provider?: 'smtp' | 'sendgrid' | 'ses'
  /** API key for SendGrid/SES */
  api_key?: string
}

/**
 * Teams notification configuration.
 */
export interface TeamsActionConfig extends ActionConfigBase {
  type: 'teams'
  /** Teams webhook URL */
  webhook_url: string
  /** Channel name for display */
  channel?: string
  /** Include detailed information */
  include_details?: boolean
  /** Message theme */
  theme?: 'auto' | 'success' | 'warning' | 'critical'
}

/**
 * Discord notification configuration.
 */
export interface DiscordActionConfig extends ActionConfigBase {
  type: 'discord'
  /** Discord webhook URL */
  webhook_url: string
  /** Bot display name */
  username?: string
  /** Bot avatar URL */
  avatar_url?: string
  /** Embed color (hex integer) */
  embed_color?: number
  /** Embed title */
  embed_title?: string
  /** Embed description */
  embed_description?: string
  /** Custom embed fields */
  embed_fields?: Array<{ name: string; value: string; inline?: boolean }>
  /** Mentions to include */
  include_mentions?: string[]
}

/**
 * Telegram notification configuration.
 */
export interface TelegramActionConfig extends ActionConfigBase {
  type: 'telegram'
  /** Telegram bot token */
  bot_token: string
  /** Channel/group ID */
  chat_id: string
  /** Parse mode */
  parse_mode?: 'Markdown' | 'HTML'
  /** Custom message template */
  message_template?: string
  /** Silent notification */
  disable_notification?: boolean
  /** Photo URL (optional) */
  photo_url?: string
}

/**
 * PagerDuty notification configuration.
 */
export interface PagerDutyActionConfig extends ActionConfigBase {
  type: 'pagerduty'
  /** PagerDuty routing key */
  routing_key: string
  /** Auto-severity mapping */
  auto_severity?: boolean
  /** Auto-resolve on success */
  auto_resolve_on_success?: boolean
  /** Deduplication key template */
  dedup_key_template?: string
  /** Custom severity override */
  severity_override?: 'critical' | 'error' | 'warning' | 'info'
}

/**
 * OpsGenie notification configuration.
 */
export interface OpsGenieActionConfig extends ActionConfigBase {
  type: 'opsgenie'
  /** OpsGenie API key */
  api_key: string
  /** Alert priority */
  priority?: 'P1' | 'P2' | 'P3' | 'P4' | 'P5'
  /** Tags for the alert */
  tags?: string[]
  /** Responders */
  responders?: Array<{
    type: 'user' | 'team' | 'escalation' | 'schedule'
    name?: string
    username?: string
    id?: string
  }>
  /** Visible to teams */
  visible_to?: Array<{
    type: 'user' | 'team'
    name?: string
    username?: string
    id?: string
  }>
  /** Auto-resolve on success */
  auto_resolve_on_success?: boolean
}

/**
 * Webhook action configuration.
 */
export interface WebhookActionConfig extends ActionConfigBase {
  type: 'webhook'
  /** Webhook URL */
  url: string
  /** HTTP method */
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH'
  /** Authentication type */
  auth_type?: 'none' | 'basic' | 'bearer' | 'api_key'
  /** Auth credentials */
  auth_credentials?: {
    username?: string
    password?: string
    token?: string
    api_key?: string
    api_key_header?: string
  }
  /** Custom headers */
  headers?: Record<string, string>
  /** Include full result in payload */
  include_full_result?: boolean
  /** Request timeout */
  request_timeout?: number
}

/**
 * File storage action configuration.
 */
export interface FileStorageActionConfig extends ActionConfigBase {
  type: 'file_storage' | 'store_result'
  /** Base path for storage */
  store_path: string
  /** Store type */
  store_type?: 'file' | 's3' | 'gcs'
  /** Output format */
  format?: 'json' | 'yaml'
  /** Partition by date, checkpoint, or status */
  partition_by?: 'date' | 'checkpoint' | 'status' | 'none'
  /** Retention days */
  retention_days?: number
  /** Compress output */
  compress?: boolean
}

/**
 * S3 storage action configuration.
 */
export interface S3StorageActionConfig extends ActionConfigBase {
  type: 's3_storage'
  /** S3 bucket */
  bucket: string
  /** Key prefix */
  prefix?: string
  /** AWS region */
  region?: string
  /** Output format */
  format?: 'json' | 'yaml' | 'parquet'
  /** Compression */
  compression?: 'gzip' | 'snappy' | 'none'
}

/**
 * GCS storage action configuration.
 */
export interface GCSStorageActionConfig extends ActionConfigBase {
  type: 'gcs_storage'
  /** GCS bucket */
  bucket: string
  /** Key prefix */
  prefix?: string
  /** GCP project */
  project?: string
  /** Output format */
  format?: 'json' | 'yaml' | 'parquet'
}

/**
 * Update DataDocs action configuration.
 */
export interface UpdateDocsActionConfig extends ActionConfigBase {
  type: 'update_docs'
  /** Site path for documentation */
  site_path: string
  /** Output format */
  format?: 'html' | 'markdown'
  /** Include history */
  include_history?: boolean
  /** Max history items */
  max_history_items?: number
  /** Template name */
  template?: 'default' | 'minimal' | 'detailed'
}

/**
 * Custom action configuration.
 */
export interface CustomActionConfig extends ActionConfigBase {
  type: 'custom' | 'callback'
  /** Python callback function path */
  callback?: string
  /** Environment variables */
  environment?: Record<string, string>
  /** Pass result as JSON */
  pass_result_as_json?: boolean
}

/**
 * Shell command action configuration.
 */
export interface ShellCommandActionConfig extends ActionConfigBase {
  type: 'shell_command'
  /** Shell command to execute */
  shell_command: string
  /** Working directory */
  working_directory?: string
  /** Environment variables */
  environment?: Record<string, string>
  /** Pass result as JSON */
  pass_result_as_json?: boolean
}

/**
 * Union type for all action configurations.
 */
export type ActionConfig =
  | SlackActionConfig
  | EmailActionConfig
  | TeamsActionConfig
  | DiscordActionConfig
  | TelegramActionConfig
  | PagerDutyActionConfig
  | OpsGenieActionConfig
  | WebhookActionConfig
  | FileStorageActionConfig
  | S3StorageActionConfig
  | GCSStorageActionConfig
  | UpdateDocsActionConfig
  | CustomActionConfig
  | ShellCommandActionConfig

// =============================================================================
// Action Result
// =============================================================================

/**
 * Result of an action execution.
 */
export interface ActionResult {
  /** Action name */
  action_name: string
  /** Action type */
  action_type: ActionType
  /** Execution status */
  status: ActionStatus
  /** Human-readable message */
  message?: string
  /** When execution started (ISO string) */
  started_at?: string
  /** When execution completed (ISO string) */
  completed_at?: string
  /** Execution duration in milliseconds */
  duration_ms?: number
  /** Additional result details */
  details?: Record<string, unknown>
  /** Error message if failed */
  error?: string
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get action type info.
 */
export function getActionTypeInfo(type: ActionType): ActionTypeInfo {
  return ACTION_TYPE_INFO[type]
}

/**
 * Get actions by category.
 */
export function getActionsByCategory(category: ActionCategory): ActionTypeInfo[] {
  return Object.values(ACTION_TYPE_INFO).filter(info => info.category === category)
}

/**
 * Create a default action config for a type.
 */
export function createDefaultActionConfig(type: ActionType, name: string): Partial<ActionConfigBase> {
  return {
    name,
    type,
    notify_on: type === 'store_result' ? 'always' : 'failure',
    enabled: true,
    timeout_seconds: 30,
    retry_count: 0,
    retry_delay_seconds: 5,
    fail_checkpoint_on_error: false,
  }
}

/**
 * Check if action status indicates success.
 */
export function isActionSuccess(status: ActionStatus): boolean {
  return status === 'success'
}

/**
 * Check if action status indicates failure.
 */
export function isActionFailed(status: ActionStatus): boolean {
  return status === 'failure'
}

/**
 * Check if action was skipped.
 */
export function isActionSkipped(status: ActionStatus): boolean {
  return status === 'skipped'
}
