/**
 * Routing types for checkpoint-based validation pipelines.
 *
 * Routing rules determine which actions to execute based on validation
 * results. They enable complex conditional logic for notifications and
 * post-validation processing.
 *
 * Features:
 * - Jinja2-based rule expressions
 * - Built-in rules (Severity, Status, Tag, etc.)
 * - Compound rules (AllOf, AnyOf, Not)
 * - Priority-based routing
 * - Context-based routing
 */

// =============================================================================
// Route Mode
// =============================================================================

/**
 * How routes are evaluated.
 */
export type RouteMode =
  | 'first_match'    // Stop at first matching route
  | 'all_matches'    // Execute all matching routes
  | 'priority'       // Execute in priority order
  | 'priority_group' // Execute highest priority group

/**
 * Human-readable labels for route modes.
 */
export const ROUTE_MODE_LABELS: Record<RouteMode, string> = {
  first_match: 'First Match',
  all_matches: 'All Matches',
  priority: 'Priority Order',
  priority_group: 'Priority Group',
}

/**
 * Descriptions for route modes.
 */
export const ROUTE_MODE_DESCRIPTIONS: Record<RouteMode, string> = {
  first_match: 'Stop at the first matching route',
  all_matches: 'Execute all matching routes',
  priority: 'Execute all matches in priority order',
  priority_group: 'Execute all routes in the highest priority group',
}

// =============================================================================
// Route Priority
// =============================================================================

/**
 * Priority levels for routes.
 */
export type RoutePriority = 'critical' | 'high' | 'medium' | 'low' | 'default'

/**
 * Numeric values for priorities.
 */
export const ROUTE_PRIORITY_VALUES: Record<RoutePriority, number> = {
  critical: 100,
  high: 75,
  medium: 50,
  low: 25,
  default: 0,
}

/**
 * Labels for priorities.
 */
export const ROUTE_PRIORITY_LABELS: Record<RoutePriority, string> = {
  critical: 'Critical (100)',
  high: 'High (75)',
  medium: 'Medium (50)',
  low: 'Low (25)',
  default: 'Default (0)',
}

// =============================================================================
// Routing Rule Types
// =============================================================================

/**
 * Available rule types.
 */
export type RoutingRuleType =
  // Simple rules
  | 'always'
  | 'never'
  | 'status'
  | 'severity'
  | 'issue_count'
  | 'pass_rate'
  | 'tag'
  | 'data_asset'
  | 'metadata'
  | 'time_window'
  | 'error'
  // Compound rules
  | 'all_of'
  | 'any_of'
  | 'not'
  // Expression rules
  | 'jinja2'
  | 'python'

/**
 * Rule type metadata.
 */
export interface RuleTypeInfo {
  type: RoutingRuleType
  label: string
  description: string
  category: 'simple' | 'compound' | 'expression'
  supportsNegate?: boolean
}

/**
 * Metadata for all rule types.
 */
export const RULE_TYPE_INFO: Record<RoutingRuleType, RuleTypeInfo> = {
  always: {
    type: 'always',
    label: 'Always',
    description: 'Always matches (default route)',
    category: 'simple',
  },
  never: {
    type: 'never',
    label: 'Never',
    description: 'Never matches (disabled route)',
    category: 'simple',
  },
  status: {
    type: 'status',
    label: 'Status',
    description: 'Match based on checkpoint status',
    category: 'simple',
    supportsNegate: true,
  },
  severity: {
    type: 'severity',
    label: 'Severity',
    description: 'Match based on issue severity levels',
    category: 'simple',
    supportsNegate: true,
  },
  issue_count: {
    type: 'issue_count',
    label: 'Issue Count',
    description: 'Match based on number of issues',
    category: 'simple',
    supportsNegate: true,
  },
  pass_rate: {
    type: 'pass_rate',
    label: 'Pass Rate',
    description: 'Match based on validation pass rate',
    category: 'simple',
    supportsNegate: true,
  },
  tag: {
    type: 'tag',
    label: 'Tag',
    description: 'Match based on checkpoint tags',
    category: 'simple',
    supportsNegate: true,
  },
  data_asset: {
    type: 'data_asset',
    label: 'Data Asset',
    description: 'Match based on data asset name pattern',
    category: 'simple',
    supportsNegate: true,
  },
  metadata: {
    type: 'metadata',
    label: 'Metadata',
    description: 'Match based on metadata values',
    category: 'simple',
    supportsNegate: true,
  },
  time_window: {
    type: 'time_window',
    label: 'Time Window',
    description: 'Match based on time of day (business hours)',
    category: 'simple',
    supportsNegate: true,
  },
  error: {
    type: 'error',
    label: 'Error',
    description: 'Match based on error occurrence',
    category: 'simple',
    supportsNegate: true,
  },
  all_of: {
    type: 'all_of',
    label: 'All Of (AND)',
    description: 'All child rules must match',
    category: 'compound',
  },
  any_of: {
    type: 'any_of',
    label: 'Any Of (OR)',
    description: 'At least one child rule must match',
    category: 'compound',
  },
  not: {
    type: 'not',
    label: 'Not',
    description: 'Invert the child rule result',
    category: 'compound',
  },
  jinja2: {
    type: 'jinja2',
    label: 'Jinja2 Expression',
    description: 'Custom Jinja2 template expression',
    category: 'expression',
  },
  python: {
    type: 'python',
    label: 'Python Expression',
    description: 'Custom Python expression (advanced)',
    category: 'expression',
  },
}

// =============================================================================
// Routing Rule Configurations
// =============================================================================

/**
 * Base rule configuration.
 */
export interface BaseRuleConfig {
  /** Rule type */
  type: RoutingRuleType
  /** Rule name */
  name?: string
  /** Rule description */
  description?: string
}

/**
 * Always rule - always matches.
 */
export interface AlwaysRuleConfig extends BaseRuleConfig {
  type: 'always'
}

/**
 * Never rule - never matches.
 */
export interface NeverRuleConfig extends BaseRuleConfig {
  type: 'never'
}

/**
 * Status rule - match by checkpoint status.
 */
export interface StatusRuleConfig extends BaseRuleConfig {
  type: 'status'
  /** Statuses to match */
  statuses: string[]
  /** Invert the match */
  negate?: boolean
}

/**
 * Severity rule - match by issue severity.
 */
export interface SeverityRuleConfig extends BaseRuleConfig {
  type: 'severity'
  /** Minimum severity to match */
  min_severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  /** Maximum severity to match */
  max_severity?: 'critical' | 'high' | 'medium' | 'low' | 'info'
  /** Minimum count of issues at this severity */
  min_count?: number
  /** Exact count of issues at this severity */
  exact_count?: number
}

/**
 * Issue count rule - match by number of issues.
 */
export interface IssueCountRuleConfig extends BaseRuleConfig {
  type: 'issue_count'
  /** Minimum issue count */
  min_issues?: number
  /** Maximum issue count */
  max_issues?: number
  /** Count type (total or by severity) */
  count_type?: 'total' | 'critical' | 'high' | 'medium' | 'low' | 'info'
}

/**
 * Pass rate rule - match by validation pass rate.
 */
export interface PassRateRuleConfig extends BaseRuleConfig {
  type: 'pass_rate'
  /** Minimum pass rate (0-100) */
  min_rate?: number
  /** Maximum pass rate (0-100) */
  max_rate?: number
}

/**
 * Tag rule - match by checkpoint tags.
 */
export interface TagRuleConfig extends BaseRuleConfig {
  type: 'tag'
  /** Tags to match (key-value pairs) */
  tags: Record<string, string | null>
  /** Match all tags (AND) or any tag (OR) */
  match_all?: boolean
  /** Invert the match */
  negate?: boolean
}

/**
 * Data asset rule - match by data asset name pattern.
 */
export interface DataAssetRuleConfig extends BaseRuleConfig {
  type: 'data_asset'
  /** Pattern to match (glob or regex) */
  pattern: string
  /** Whether pattern is regex */
  is_regex?: boolean
  /** Case sensitive matching */
  case_sensitive?: boolean
}

/**
 * Metadata rule - match by metadata values.
 */
export interface MetadataRuleConfig extends BaseRuleConfig {
  type: 'metadata'
  /** Dot-separated key path */
  key_path: string
  /** Expected value */
  expected_value?: unknown
  /** Comparison operator */
  comparator?: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'regex' | 'exists'
}

/**
 * Time window rule - match by time of day.
 */
export interface TimeWindowRuleConfig extends BaseRuleConfig {
  type: 'time_window'
  /** Start time (HH:MM format) */
  start_time?: string
  /** End time (HH:MM format) */
  end_time?: string
  /** Days of week (0=Monday, 6=Sunday) */
  days_of_week?: number[]
  /** Timezone */
  timezone?: string
}

/**
 * Error rule - match on error occurrence.
 */
export interface ErrorRuleConfig extends BaseRuleConfig {
  type: 'error'
  /** Error pattern to match (regex) */
  pattern?: string
  /** Invert the match (match if no error) */
  negate?: boolean
}

/**
 * AllOf rule - all child rules must match.
 */
export interface AllOfRuleConfig extends BaseRuleConfig {
  type: 'all_of'
  /** Child rules */
  rules: RoutingRule[]
}

/**
 * AnyOf rule - any child rule must match.
 */
export interface AnyOfRuleConfig extends BaseRuleConfig {
  type: 'any_of'
  /** Child rules */
  rules: RoutingRule[]
}

/**
 * Not rule - invert child rule.
 */
export interface NotRuleConfig extends BaseRuleConfig {
  type: 'not'
  /** Child rule */
  rule: RoutingRule
}

/**
 * Jinja2 rule - custom expression.
 */
export interface Jinja2RuleConfig extends BaseRuleConfig {
  type: 'jinja2'
  /** Jinja2 expression */
  expression: string
}

/**
 * Python rule - custom Python expression.
 */
export interface PythonRuleConfig extends BaseRuleConfig {
  type: 'python'
  /** Python expression */
  expression: string
}

/**
 * Union type for all routing rules.
 */
export type RoutingRule =
  | AlwaysRuleConfig
  | NeverRuleConfig
  | StatusRuleConfig
  | SeverityRuleConfig
  | IssueCountRuleConfig
  | PassRateRuleConfig
  | TagRuleConfig
  | DataAssetRuleConfig
  | MetadataRuleConfig
  | TimeWindowRuleConfig
  | ErrorRuleConfig
  | AllOfRuleConfig
  | AnyOfRuleConfig
  | NotRuleConfig
  | Jinja2RuleConfig
  | PythonRuleConfig

// =============================================================================
// Route Definition
// =============================================================================

/**
 * A route defines a rule and its associated actions.
 */
export interface Route {
  /** Route name for identification */
  name: string
  /** Routing rule to evaluate */
  rule: RoutingRule
  /** Action names to execute when rule matches */
  actions: string[]
  /** Priority for route ordering */
  priority?: RoutePriority | number
  /** Whether this route is enabled */
  enabled?: boolean
  /** Additional metadata */
  metadata?: Record<string, unknown>
  /** Stop evaluating other routes after this one matches */
  stop_on_match?: boolean
  /** Description */
  description?: string
}

/**
 * Router configuration.
 */
export interface Router {
  /** Routing mode */
  mode: RouteMode
  /** Routes */
  routes: Route[]
}

// =============================================================================
// Route Context (for rule evaluation)
// =============================================================================

/**
 * Context passed to routing rule evaluation.
 */
export interface RouteContext {
  /** Checkpoint name */
  checkpoint_name: string
  /** Run ID */
  run_id: string
  /** Checkpoint status */
  status: string
  /** Data asset */
  data_asset?: string
  /** Run time (ISO string) */
  run_time?: string
  /** Total issue count */
  total_issues?: number
  /** Critical issue count */
  critical_issues?: number
  /** High issue count */
  high_issues?: number
  /** Medium issue count */
  medium_issues?: number
  /** Low issue count */
  low_issues?: number
  /** Info issue count */
  info_issues?: number
  /** Pass rate (0-100) */
  pass_rate?: number
  /** Tags */
  tags?: Record<string, string>
  /** Metadata */
  metadata?: Record<string, unknown>
  /** Validation duration (ms) */
  validation_duration_ms?: number
  /** Error message */
  error?: string | null
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get rule type info.
 */
export function getRuleTypeInfo(type: RoutingRuleType): RuleTypeInfo {
  return RULE_TYPE_INFO[type]
}

/**
 * Get rules by category.
 */
export function getRulesByCategory(category: 'simple' | 'compound' | 'expression'): RuleTypeInfo[] {
  return Object.values(RULE_TYPE_INFO).filter(info => info.category === category)
}

/**
 * Create a default rule config for a type.
 */
export function createDefaultRuleConfig(type: RoutingRuleType): RoutingRule {
  switch (type) {
    case 'always':
      return { type: 'always' }
    case 'never':
      return { type: 'never' }
    case 'status':
      return { type: 'status', statuses: ['failure'] }
    case 'severity':
      return { type: 'severity', min_severity: 'high' }
    case 'issue_count':
      return { type: 'issue_count', min_issues: 1 }
    case 'pass_rate':
      return { type: 'pass_rate', max_rate: 90 }
    case 'tag':
      return { type: 'tag', tags: {} }
    case 'data_asset':
      return { type: 'data_asset', pattern: '*' }
    case 'metadata':
      return { type: 'metadata', key_path: '' }
    case 'time_window':
      return { type: 'time_window', start_time: '09:00', end_time: '17:00' }
    case 'error':
      return { type: 'error' }
    case 'all_of':
      return { type: 'all_of', rules: [] }
    case 'any_of':
      return { type: 'any_of', rules: [] }
    case 'not':
      return { type: 'not', rule: { type: 'always' } }
    case 'jinja2':
      return { type: 'jinja2', expression: 'failed' }
    case 'python':
      return { type: 'python', expression: '' }
    default:
      return { type: 'always' }
  }
}

/**
 * Convert a rule to a human-readable description.
 */
export function describeRule(rule: RoutingRule): string {
  switch (rule.type) {
    case 'always':
      return 'Always'
    case 'never':
      return 'Never'
    case 'status':
      return `Status in [${rule.statuses.join(', ')}]${rule.negate ? ' (inverted)' : ''}`
    case 'severity':
      return `Severity >= ${rule.min_severity}${rule.min_count ? ` (min ${rule.min_count})` : ''}`
    case 'issue_count':
      return `Issues ${rule.min_issues ? `>= ${rule.min_issues}` : ''}${rule.max_issues ? ` <= ${rule.max_issues}` : ''}`
    case 'pass_rate':
      return `Pass rate ${rule.min_rate ? `>= ${rule.min_rate}%` : ''}${rule.max_rate ? ` <= ${rule.max_rate}%` : ''}`
    case 'tag':
      return `Tags: ${Object.entries(rule.tags).map(([k, v]) => v ? `${k}=${v}` : k).join(', ')}`
    case 'data_asset':
      return `Asset matches "${rule.pattern}"`
    case 'time_window':
      return `Time: ${rule.start_time || '00:00'} - ${rule.end_time || '23:59'}`
    case 'error':
      return rule.pattern ? `Error matches "${rule.pattern}"` : 'Has error'
    case 'all_of':
      return `All of (${rule.rules.length} rules)`
    case 'any_of':
      return `Any of (${rule.rules.length} rules)`
    case 'not':
      return `Not (${describeRule(rule.rule)})`
    case 'jinja2':
      return `Expression: ${rule.expression}`
    case 'metadata':
      return `Metadata: ${rule.key_path} ${rule.comparator || '=='} ${rule.expected_value}`
    case 'python':
      return `Python: ${rule.expression.substring(0, 50)}...`
    default:
      return 'Unknown rule'
  }
}

/**
 * Validate a route configuration.
 */
export function validateRoute(route: Route): string[] {
  const errors: string[] = []

  if (!route.name?.trim()) {
    errors.push('Route name is required')
  }

  if (!route.rule) {
    errors.push('Route rule is required')
  }

  if (!route.actions || route.actions.length === 0) {
    errors.push('At least one action is required')
  }

  return errors
}
