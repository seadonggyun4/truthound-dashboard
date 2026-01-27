/**
 * Charts API - Chart settings and configuration.
 */
import { request } from '../core'

// ============================================================================
// Types
// ============================================================================

export type ChartLibrary = 'recharts' | 'chartjs' | 'echarts' | 'plotly' | 'svg'

export interface ChartLibraryConfig {
  library: ChartLibrary
  npm_package: string
  version: string
  supported_charts: string[]
  cdn_url: string | null
}

export interface ChartSettings {
  library: ChartLibrary
  theme: string
  primary_color: string
  animation_enabled: boolean
  default_height: number
  custom_options: Record<string, unknown>
  library_config: ChartLibraryConfig
  available_libraries: {
    library: ChartLibrary
    name: string
    npm_package: string
    supported_charts: string[]
  }[]
}

// ============================================================================
// API Functions
// ============================================================================

export async function getChartSettings(): Promise<ChartSettings> {
  return request<ChartSettings>('/settings/charts')
}

export async function updateChartSettings(settings: {
  library?: ChartLibrary
  theme?: string
  primary_color?: string
  animation_enabled?: boolean
  default_height?: number
  custom_options?: Record<string, unknown>
}): Promise<ChartSettings> {
  return request<ChartSettings>('/settings/charts', {
    method: 'PUT',
    body: JSON.stringify(settings),
  })
}
