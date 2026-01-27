/**
 * Rule Suggestions API - AI-powered validation rule generation.
 */
import { request, ApiError } from '../core'

// ============================================================================
// Types
// ============================================================================

export type StrictnessLevel = 'loose' | 'medium' | 'strict'

export type RulePreset =
  | 'default'
  | 'strict'
  | 'loose'
  | 'minimal'
  | 'comprehensive'
  | 'ci_cd'
  | 'schema_only'
  | 'format_only'

export type RuleExportFormat = 'yaml' | 'json' | 'python' | 'toml'

export type RuleCategory =
  | 'schema'
  | 'stats'
  | 'pattern'
  | 'completeness'
  | 'uniqueness'
  | 'distribution'
  | 'relationship'
  | 'multi_column'

export interface SuggestedRule {
  id: string
  column: string
  validator_name: string
  params: Record<string, unknown>
  confidence: number
  reason: string
  severity_suggestion: string
  category: RuleCategory | string
}

export type CrossColumnRuleType =
  | 'composite_key'
  | 'column_sum'
  | 'column_product'
  | 'column_difference'
  | 'column_ratio'
  | 'column_percentage'
  | 'column_comparison'
  | 'column_chain_comparison'
  | 'column_dependency'
  | 'column_implication'
  | 'column_coexistence'
  | 'column_mutual_exclusivity'
  | 'column_correlation'
  | 'referential_integrity'

export interface CrossColumnRuleSuggestion {
  id: string
  rule_type: CrossColumnRuleType
  columns: string[]
  validator_name: string
  params: Record<string, unknown>
  confidence: number
  reason: string
  severity_suggestion: string
  evidence: Record<string, unknown>
  sample_violations: Array<Record<string, unknown>>
}

export interface RuleSuggestionRequest {
  use_latest_profile?: boolean
  profile_id?: string
  min_confidence?: number
  strictness?: StrictnessLevel
  preset?: RulePreset
  include_categories?: RuleCategory[]
  exclude_categories?: RuleCategory[]
  include_types?: string[]
  exclude_columns?: string[]
  enable_cross_column?: boolean
  include_cross_column_types?: CrossColumnRuleType[]
  exclude_cross_column_types?: CrossColumnRuleType[]
}

export interface RuleSuggestionResponse {
  source_id: string
  source_name: string
  profile_id: string
  suggestions: SuggestedRule[]
  total_suggestions: number
  high_confidence_count: number
  generated_at: string
  strictness: StrictnessLevel
  preset: RulePreset | null
  categories_included: RuleCategory[]
  by_category: Record<string, number>
  cross_column_suggestions?: CrossColumnRuleSuggestion[]
  cross_column_count?: number
  by_cross_column_type?: Record<string, number>
}

export interface ApplyRulesRequest {
  suggestions?: SuggestedRule[]
  rule_ids?: string[]
  create_new_rule?: boolean
  rule_name?: string
  rule_description?: string
}

export interface ApplyRulesResponse {
  source_id: string
  rule_id: string
  rule_name: string
  applied_count: number
  validators: string[]
  created_at: string
}

export interface ExportRulesRequest {
  suggestions: SuggestedRule[]
  format: RuleExportFormat
  include_metadata?: boolean
  rule_name?: string
  description?: string
}

export interface ExportRulesResponse {
  content: string
  format: RuleExportFormat
  filename: string
  rule_count: number
  generated_at: string
}

export interface PresetInfo {
  name: RulePreset
  display_name: string
  description: string
  strictness: StrictnessLevel
  categories: RuleCategory[]
  recommended_for: string
}

export interface PresetsResponse {
  presets: PresetInfo[]
  strictness_levels: StrictnessLevel[]
  categories: RuleCategory[]
  export_formats: RuleExportFormat[]
}

// ============================================================================
// API Functions
// ============================================================================

const API_BASE = '/api/v1'

export async function suggestRules(
  sourceId: string,
  options?: RuleSuggestionRequest
): Promise<RuleSuggestionResponse> {
  return request(`/sources/${sourceId}/rules/suggest`, {
    method: 'POST',
    body: JSON.stringify(options || {}),
  })
}

export async function applyRuleSuggestions(
  sourceId: string,
  data: ApplyRulesRequest
): Promise<ApplyRulesResponse> {
  return request(`/sources/${sourceId}/rules/apply-suggestions`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function exportRules(
  sourceId: string,
  data: ExportRulesRequest
): Promise<ExportRulesResponse> {
  return request(`/sources/${sourceId}/rules/export`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function downloadExportedRules(
  sourceId: string,
  data: ExportRulesRequest
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/sources/${sourceId}/rules/export/download`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText)
  }
  return response.blob()
}

export async function getRuleSuggestionPresets(): Promise<PresetsResponse> {
  return request('/rule-suggestions/presets')
}
