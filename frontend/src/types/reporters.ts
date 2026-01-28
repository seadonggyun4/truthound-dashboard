/**
 * Reporter system types for truthound-dashboard.
 *
 * This module provides TypeScript types matching the backend reporter system,
 * enabling type-safe configuration and generation of validation reports.
 *
 * Based on truthound reporters documentation:
 * - Multiple formats: HTML, CSV, JSON
 * - Unified interface: BaseReporter with render(), write() methods
 * - ValidationReporter for validation-specific reports
 * - CI Platform reporters: GitHub Actions, GitLab CI, Azure DevOps, Jenkins
 * - Mixin-based extensibility (Formatting, Aggregation, Filtering)
 * - SDK for custom reporter development using decorators or builder pattern
 *
 * Important distinction:
 * - Report (from th.check()): Simple report with issues list, has_issues, print(), to_json()
 * - ValidationResult: Storage-oriented with run_id, statistics, tags for full reporter functionality
 */

// =============================================================================
// Enums and Constants
// =============================================================================

/**
 * Supported report output formats.
 * Maps to backend ReportFormatType enum.
 */
export type ReportFormatType =
  | 'html'
  | 'csv'
  | 'json'
  | 'yaml'
  | 'ndjson'
  | 'console'
  | 'table'

/**
 * CI platform reporter types.
 * Maps to truthound.reporters.ci module.
 */
export type CIPlatformType =
  | 'github'    // GitHub Actions
  | 'gitlab'    // GitLab CI
  | 'azure'     // Azure DevOps
  | 'jenkins'   // Jenkins
  | 'ci'        // Auto-detect CI platform

/**
 * Report visual themes.
 */
export type ReportThemeType =
  | 'light'
  | 'dark'
  | 'professional'
  | 'minimal'
  | 'high_contrast'

/**
 * Report generation status.
 */
export type ReportStatus =
  | 'pending'
  | 'generating'
  | 'completed'
  | 'failed'
  | 'expired'

/**
 * Supported locales for report i18n.
 * 15 languages as per truthound documentation.
 */
export type ReportLocale =
  | 'en'
  | 'ko'
  | 'ja'
  | 'zh'
  | 'de'
  | 'fr'
  | 'es'
  | 'pt'
  | 'it'
  | 'ru'
  | 'ar'
  | 'th'
  | 'vi'
  | 'id'
  | 'tr'

/**
 * Format information for display.
 */
export interface ReportFormatInfo {
  value: ReportFormatType
  label: string
  description: string
  icon?: string
  extension: string
  contentType: string
  supportsTheme: boolean
  supportsI18n: boolean
  requiresDependency?: string
}

/**
 * Available report formats with metadata.
 */
export const REPORT_FORMATS: ReportFormatInfo[] = [
  {
    value: 'html',
    label: 'HTML',
    description: 'Interactive web report with charts and styling',
    icon: 'file-code',
    extension: '.html',
    contentType: 'text/html',
    supportsTheme: true,
    supportsI18n: true,
  },
  {
    value: 'json',
    label: 'JSON',
    description: 'Structured data for API integration',
    icon: 'braces',
    extension: '.json',
    contentType: 'application/json',
    supportsTheme: false,
    supportsI18n: false,
  },
  {
    value: 'csv',
    label: 'CSV',
    description: 'Tabular data for spreadsheet analysis',
    icon: 'file-spreadsheet',
    extension: '.csv',
    contentType: 'text/csv',
    supportsTheme: false,
    supportsI18n: false,
  },
]

/**
 * Theme information for display.
 */
export interface ReportThemeInfo {
  value: ReportThemeType
  label: string
  description: string
  preview?: string
}

/**
 * Available themes with metadata.
 */
export const REPORT_THEMES: ReportThemeInfo[] = [
  {
    value: 'professional',
    label: 'Professional',
    description: 'Clean, business-ready styling',
  },
  {
    value: 'light',
    label: 'Light',
    description: 'Light background with dark text',
  },
  {
    value: 'dark',
    label: 'Dark',
    description: 'Dark background with light text',
  },
  {
    value: 'minimal',
    label: 'Minimal',
    description: 'Simple, distraction-free layout',
  },
  {
    value: 'high_contrast',
    label: 'High Contrast',
    description: 'Accessibility-focused high contrast',
  },
]

/**
 * Locale information for display.
 */
export interface LocaleInfo {
  code: ReportLocale
  englishName: string
  nativeName: string
  flag: string
  rtl: boolean
}

/**
 * Available locales with metadata.
 */
export const REPORT_LOCALES: LocaleInfo[] = [
  { code: 'en', englishName: 'English', nativeName: 'English', flag: '🇺🇸', rtl: false },
  { code: 'ko', englishName: 'Korean', nativeName: '한국어', flag: '🇰🇷', rtl: false },
  { code: 'ja', englishName: 'Japanese', nativeName: '日本語', flag: '🇯🇵', rtl: false },
  { code: 'zh', englishName: 'Chinese', nativeName: '中文', flag: '🇨🇳', rtl: false },
  { code: 'de', englishName: 'German', nativeName: 'Deutsch', flag: '🇩🇪', rtl: false },
  { code: 'fr', englishName: 'French', nativeName: 'Français', flag: '🇫🇷', rtl: false },
  { code: 'es', englishName: 'Spanish', nativeName: 'Español', flag: '🇪🇸', rtl: false },
  { code: 'pt', englishName: 'Portuguese', nativeName: 'Português', flag: '🇵🇹', rtl: false },
  { code: 'it', englishName: 'Italian', nativeName: 'Italiano', flag: '🇮🇹', rtl: false },
  { code: 'ru', englishName: 'Russian', nativeName: 'Русский', flag: '🇷🇺', rtl: false },
  { code: 'ar', englishName: 'Arabic', nativeName: 'العربية', flag: '🇸🇦', rtl: true },
  { code: 'th', englishName: 'Thai', nativeName: 'ไทย', flag: '🇹🇭', rtl: false },
  { code: 'vi', englishName: 'Vietnamese', nativeName: 'Tiếng Việt', flag: '🇻🇳', rtl: false },
  { code: 'id', englishName: 'Indonesian', nativeName: 'Bahasa Indonesia', flag: '🇮🇩', rtl: false },
  { code: 'tr', englishName: 'Turkish', nativeName: 'Türkçe', flag: '🇹🇷', rtl: false },
]

// =============================================================================
// Configuration Types
// =============================================================================

/**
 * Configuration for report generation.
 * Maps to backend ReporterConfig dataclass.
 */
export interface ReporterConfig {
  /** Report title */
  title?: string
  /** Visual theme */
  theme?: ReportThemeType
  /** Language locale code */
  locale?: ReportLocale
  /** Include sample values in output */
  includeSamples?: boolean
  /** Include statistics section */
  includeStatistics?: boolean
  /** Include report metadata */
  includeMetadata?: boolean
  /** Maximum sample values to include */
  maxSampleValues?: number
  /** Date/time format string */
  timestampFormat?: string
  /** Backend-specific options */
  customOptions?: Record<string, unknown>
}

/**
 * Default configuration values.
 */
export const DEFAULT_REPORTER_CONFIG: Required<ReporterConfig> = {
  title: 'Validation Report',
  theme: 'professional',
  locale: 'en',
  includeSamples: true,
  includeStatistics: true,
  includeMetadata: true,
  maxSampleValues: 5,
  timestampFormat: '%Y-%m-%d %H:%M:%S',
  customOptions: {},
}

// =============================================================================
// Data Types
// =============================================================================

/**
 * Issue severity levels for reports.
 * Uses same values as validator IssueSeverity but kept as separate type for reports module.
 */
export type ReportIssueSeverity = 'low' | 'medium' | 'high' | 'critical'

/**
 * Validation issue data for reports.
 */
export interface ValidationIssueData {
  column: string | null
  issueType: string
  severity: ReportIssueSeverity
  message: string
  count: number
  expected?: unknown
  actual?: unknown
  sampleValues?: unknown[]
  validatorName?: string
  details?: Record<string, unknown>
}

/**
 * Summary statistics for validation results.
 */
export interface ValidationSummary {
  totalIssues: number
  criticalIssues: number
  highIssues: number
  mediumIssues: number
  lowIssues: number
  passed: boolean
}

/**
 * Data statistics for reports.
 */
export interface DataStatistics {
  rowCount?: number
  columnCount?: number
  durationMs?: number
  startedAt?: string
  completedAt?: string
}

/**
 * Input data for report generation.
 * Maps to backend ReportData dataclass.
 */
export interface ReportData {
  validationId: string
  sourceId: string
  sourceName?: string
  issues: ValidationIssueData[]
  summary: ValidationSummary
  statistics: DataStatistics
  status: string
  errorMessage?: string
  metadata?: Record<string, unknown>
}

/**
 * Output from report generation.
 * Maps to backend ReportOutput dataclass.
 */
export interface ReportOutput {
  content: string
  contentType: string
  filename: string
  format: ReportFormatType
  sizeBytes: number
  generationTimeMs: number
  metadata?: Record<string, unknown>
}

// =============================================================================
// Generated Report Types
// =============================================================================

/**
 * Generated report record from history.
 */
export interface GeneratedReport {
  id: string
  name: string
  format: ReportFormatType
  description?: string
  theme?: ReportThemeType
  locale?: ReportLocale
  config?: Record<string, unknown>
  metadata?: Record<string, unknown>
  validationId?: string
  sourceId?: string
  reporterId?: string
  status: ReportStatus
  filePath?: string
  fileSize?: number
  generationTimeMs?: number
  downloadCount: number
  expiresAt?: string
  createdAt: string
  updatedAt: string
  // Enriched fields
  sourceName?: string
  reporterName?: string
  downloadUrl?: string
}

/**
 * Options for creating a report record.
 */
export interface ReportCreateOptions {
  name: string
  format: ReportFormatType
  validationId?: string
  sourceId?: string
  reporterId?: string
  description?: string
  theme?: ReportThemeType
  locale?: ReportLocale
  config?: Record<string, unknown>
  metadata?: Record<string, unknown>
  expiresInDays?: number
}

/**
 * Options for updating a report record.
 */
export interface ReportUpdateOptions {
  name?: string
  description?: string
  metadata?: Record<string, unknown>
}

/**
 * Report statistics.
 */
export interface ReportStatistics {
  totalReports: number
  totalSizeBytes: number
  reportsByFormat: Record<string, number>
  reportsByStatus: Record<string, number>
  totalDownloads: number
  avgGenerationTimeMs?: number
  expiredCount: number
  reportersUsed: number
}

// =============================================================================
// Custom Reporter Types
// =============================================================================

/**
 * Custom reporter output format.
 */
export type ReporterOutputFormat = 'string' | 'bytes' | 'json' | 'html'

/**
 * Custom reporter definition.
 */
export interface CustomReporter {
  id: string
  pluginId?: string
  name: string
  displayName: string
  description?: string
  version: string
  category?: string
  fileExtension: string
  contentType: string
  supportsTheme: boolean
  supportsI18n: boolean
  template?: string
  code?: string
  configSchema?: Record<string, unknown>
  defaultConfig?: Record<string, unknown>
  enabled: boolean
  builtIn: boolean
  createdAt: string
  updatedAt: string
}

/**
 * Options for creating a custom reporter.
 */
export interface CustomReporterCreateOptions {
  name: string
  displayName: string
  description?: string
  version?: string
  category?: string
  fileExtension: string
  contentType: string
  supportsTheme?: boolean
  supportsI18n?: boolean
  template?: string
  code?: string
  configSchema?: Record<string, unknown>
  defaultConfig?: Record<string, unknown>
}

// =============================================================================
// API Response Types
// =============================================================================

/**
 * Available formats response from API.
 */
export interface AvailableFormatsResponse {
  formats: string[]
  themes: string[]
  locales: LocaleInfo[]
}

/**
 * Paginated list response.
 */
export interface ReportListResponse {
  items: GeneratedReport[]
  total: number
  page: number
  pageSize: number
}

/**
 * Bulk report generation request.
 */
export interface BulkReportRequest {
  validationIds: string[]
  format?: ReportFormatType
  theme?: ReportThemeType
  locale?: ReportLocale
  reporterId?: string
  config?: Record<string, unknown>
  saveToHistory?: boolean
  expiresInDays?: number
}

/**
 * Bulk report generation response.
 */
export interface BulkReportResponse {
  total: number
  successful: number
  failed: number
  reports: GeneratedReport[]
  errors: Array<{ validationId: string; error: string }>
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get format info by value.
 */
export function getFormatInfo(format: ReportFormatType): ReportFormatInfo | undefined {
  return REPORT_FORMATS.find((f) => f.value === format)
}

/**
 * Get theme info by value.
 */
export function getThemeInfo(theme: ReportThemeType): ReportThemeInfo | undefined {
  return REPORT_THEMES.find((t) => t.value === theme)
}

/**
 * Get locale info by code.
 */
export function getLocaleInfo(code: ReportLocale): LocaleInfo | undefined {
  return REPORT_LOCALES.find((l) => l.code === code)
}

/**
 * Check if a format supports theming.
 */
export function formatSupportsTheme(format: ReportFormatType): boolean {
  const info = getFormatInfo(format)
  return info?.supportsTheme ?? false
}

/**
 * Check if a format supports i18n.
 */
export function formatSupportsI18n(format: ReportFormatType): boolean {
  const info = getFormatInfo(format)
  return info?.supportsI18n ?? false
}

/**
 * Get file extension for a format.
 */
export function getFormatExtension(format: ReportFormatType): string {
  const info = getFormatInfo(format)
  return info?.extension ?? `.${format}`
}

/**
 * Get content type for a format.
 */
export function getFormatContentType(format: ReportFormatType): string {
  const info = getFormatInfo(format)
  return info?.contentType ?? 'application/octet-stream'
}

/**
 * Create default reporter config.
 */
export function createDefaultConfig(overrides?: Partial<ReporterConfig>): ReporterConfig {
  return {
    ...DEFAULT_REPORTER_CONFIG,
    ...overrides,
  }
}

/**
 * Format file size for display.
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`
}

/**
 * Format generation time for display.
 */
export function formatGenerationTime(ms: number | undefined): string {
  if (!ms) return '-'
  if (ms < 1000) return `${ms.toFixed(0)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

/**
 * Check if report is downloadable.
 */
export function isReportDownloadable(report: GeneratedReport): boolean {
  return report.status === 'completed' && !!report.filePath
}

/**
 * Check if report is expired.
 */
export function isReportExpired(report: GeneratedReport): boolean {
  if (!report.expiresAt) return false
  return new Date(report.expiresAt) < new Date()
}

/**
 * Get status badge variant.
 */
export function getStatusVariant(
  status: ReportStatus
): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (status) {
    case 'completed':
      return 'default'
    case 'generating':
      return 'secondary'
    case 'failed':
      return 'destructive'
    case 'pending':
    case 'expired':
    default:
      return 'outline'
  }
}

// =============================================================================
// ValidationResult Types (for full reporter functionality)
// =============================================================================

/**
 * Result status for validation runs.
 * Maps to truthound.stores.results.ResultStatus.
 */
export type ResultStatus = 'success' | 'failure' | 'error' | 'skipped'

/**
 * Severity levels for validation issues.
 */
export type IssueSeverity = 'critical' | 'error' | 'warning' | 'info'

/**
 * Individual validator result.
 * Maps to truthound.stores.results.ValidatorResult.
 */
export interface ValidatorResult {
  validatorName: string
  column?: string
  success: boolean
  issueType?: string
  severity?: IssueSeverity
  message?: string
  count?: number
  expected?: unknown
  actual?: unknown
  sampleValues?: unknown[]
  details?: Record<string, unknown>
  durationMs?: number
}

/**
 * Statistics for validation results.
 * Maps to truthound.stores.results.ResultStatistics.
 */
export interface ResultStatistics {
  totalIssues: number
  totalRows?: number
  totalColumns?: number
  criticalCount: number
  errorCount: number
  warningCount: number
  infoCount: number
  passedValidators: number
  failedValidators: number
  skippedValidators: number
  durationMs: number
}

/**
 * Full validation result for reporters.
 * Maps to truthound.stores.results.ValidationResult.
 *
 * This is what reporters expect as input, not the simple Report from th.check().
 */
export interface ValidationResult {
  runId: string
  runTime: string
  dataAsset: string
  status: ResultStatus
  results: ValidatorResult[]
  statistics: ResultStatistics
  tags?: string[]
  metadata?: Record<string, unknown>
}

// =============================================================================
// CI Platform Reporter Types
// =============================================================================

/**
 * CI platform information for auto-detection.
 */
export interface CIPlatformInfo {
  id: CIPlatformType
  name: string
  description: string
  icon: string
  outputFormat: string
  envVariables: string[]
}

/**
 * Available CI platforms.
 */
export const CI_PLATFORMS: CIPlatformInfo[] = [
  {
    id: 'github',
    name: 'GitHub Actions',
    description: 'Outputs ::error:: and ::warning:: annotations',
    icon: 'github',
    outputFormat: 'annotations',
    envVariables: ['GITHUB_ACTIONS'],
  },
  {
    id: 'gitlab',
    name: 'GitLab CI',
    description: 'Outputs section markers and artifacts',
    icon: 'gitlab',
    outputFormat: 'sections',
    envVariables: ['GITLAB_CI'],
  },
  {
    id: 'azure',
    name: 'Azure DevOps',
    description: 'Outputs ##vso[task.logissue] commands',
    icon: 'cloud',
    outputFormat: 'vso_commands',
    envVariables: ['AZURE_PIPELINES', 'TF_BUILD'],
  },
  {
    id: 'jenkins',
    name: 'Jenkins',
    description: 'Standard console output with markers',
    icon: 'construction',
    outputFormat: 'console',
    envVariables: ['JENKINS_URL', 'BUILD_NUMBER'],
  },
]

/**
 * Get CI platform info by ID.
 */
export function getCIPlatformInfo(id: CIPlatformType): CIPlatformInfo | undefined {
  return CI_PLATFORMS.find((p) => p.id === id)
}

// =============================================================================
// Reporter SDK Types
// =============================================================================

/**
 * Reporter mixin capabilities.
 * Based on truthound.reporters.sdk mixins.
 */
export type ReporterMixin =
  | 'formatting'      // FormattingMixin - date/number formatting
  | 'filtering'       // FilteringMixin - filter results
  | 'aggregation'     // AggregationMixin - group by severity/column

/**
 * Custom reporter created via SDK.
 */
export interface SDKReporter {
  name: string
  displayName: string
  fileExtension: string
  contentType: string
  description?: string
  mixins: ReporterMixin[]
  /** Template string for Jinja2-based reporters */
  template?: string
  /** Python code for code-based reporters */
  code?: string
  /** Configuration schema */
  configSchema?: Record<string, unknown>
}

/**
 * Reporter builder options for fluent API.
 */
export interface ReporterBuilderOptions {
  name: string
  extension?: string
  contentType?: string
  renderer?: string
  configClass?: string
  mixins?: ReporterMixin[]
}

// =============================================================================
// Report Generation Request/Response
// =============================================================================

/**
 * Request to generate a report.
 */
export interface GenerateReportRequest {
  /** Validation result or ID */
  validationId?: string
  validationResult?: ValidationResult
  /** Report format */
  format: ReportFormatType
  /** Reporter configuration */
  config?: ReporterConfig
  /** Custom reporter ID (if using custom reporter) */
  reporterId?: string
  /** Save to report history */
  saveToHistory?: boolean
  /** Report name for history */
  name?: string
  /** Expiration in days */
  expiresInDays?: number
}

/**
 * Response from report generation.
 */
export interface GenerateReportResponse {
  /** Generated report content (base64 for binary formats) */
  content: string
  /** Content type */
  contentType: string
  /** Suggested filename */
  filename: string
  /** Format used */
  format: ReportFormatType
  /** Size in bytes */
  sizeBytes: number
  /** Generation time in ms */
  generationTimeMs: number
  /** Report record if saved to history */
  report?: GeneratedReport
}

/**
 * Preview request for custom reporters.
 */
export interface ReporterPreviewRequest {
  reporterId: string
  sampleData?: ValidationResult
  config?: ReporterConfig
}

/**
 * Preview response.
 */
export interface ReporterPreviewResponse {
  content: string
  contentType: string
  previewUrl?: string
}
