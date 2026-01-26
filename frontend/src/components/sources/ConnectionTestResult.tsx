/**
 * ConnectionTestResult - Reusable component for displaying connection test results
 *
 * Shows success/failure status with detailed feedback including:
 * - Connection status with appropriate icons
 * - Row/column counts when available
 * - Data source capabilities
 * - Error messages with troubleshooting hints
 * - Loading state during test
 */

import {
  CheckCircle,
  AlertCircle,
  Loader2,
  Database,
  Table,
  Clock,
  Server,
  Info,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import {
  SourceCapabilities,
  CapabilityBadge,
} from '@/components/sources/SourceCapabilities'
import type {
  DataSourceCapability,
  ColumnType,
  ConnectionTestResult as ConnectionTestResultType,
  ConnectionTestMetadata,
} from '@/types/datasources'

// ============================================================================
// Types
// ============================================================================

export interface ConnectionTestResultData {
  success: boolean
  message?: string
  error?: string
  /** Test duration in milliseconds */
  latency_ms?: number
  /** Additional metadata from connection test */
  metadata?: ConnectionTestMetadata
}

interface ConnectionTestResultProps {
  /** Test result data */
  result: ConnectionTestResultData | null
  /** Whether a test is currently running */
  testing?: boolean
  /** Custom class name */
  className?: string
  /** Show capabilities badges */
  showCapabilities?: boolean
  /** Compact mode - less padding, smaller text */
  compact?: boolean
}

// ============================================================================
// Main Component
// ============================================================================

export function ConnectionTestResult({
  result,
  testing,
  className,
  showCapabilities = true,
  compact = false,
}: ConnectionTestResultProps) {
  if (testing) {
    return (
      <div
        className={cn(
          'flex items-center gap-3 rounded-lg bg-muted/50 transition-all',
          compact ? 'p-3' : 'p-4',
          className
        )}
      >
        <Loader2 className="h-5 w-5 animate-spin text-primary" />
        <div className="text-sm text-muted-foreground">
          Testing connection...
        </div>
      </div>
    )
  }

  if (!result) return null

  return (
    <div
      className={cn(
        'rounded-lg transition-all',
        compact ? 'p-3' : 'p-4',
        result.success
          ? 'bg-green-500/10 border border-green-500/20'
          : 'bg-destructive/10 border border-destructive/20',
        className
      )}
    >
      <div className="flex items-start gap-3">
        {result.success ? (
          <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-green-600 dark:text-green-400" />
        ) : (
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-destructive" />
        )}

        <div className="flex-1 space-y-2">
          {/* Main message */}
          <div
            className={cn(
              'font-medium',
              compact ? 'text-xs' : 'text-sm',
              result.success
                ? 'text-green-700 dark:text-green-400'
                : 'text-destructive'
            )}
          >
            {result.success
              ? result.message || 'Connection successful!'
              : result.error || 'Connection failed'}
          </div>

          {/* Metadata for successful connections */}
          {result.success && result.metadata && (
            <ConnectionMetadata
              metadata={result.metadata}
              latencyMs={result.latency_ms}
              showCapabilities={showCapabilities}
              compact={compact}
            />
          )}

          {/* Error troubleshooting hints */}
          {!result.success && result.error && (
            <TroubleshootingHints error={result.error} compact={compact} />
          )}
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Metadata Display
// ============================================================================

interface ConnectionMetadataProps {
  metadata: ConnectionTestMetadata
  latencyMs?: number
  showCapabilities?: boolean
  compact?: boolean
}

function ConnectionMetadata({
  metadata,
  latencyMs,
  showCapabilities = true,
  compact = false,
}: ConnectionMetadataProps) {
  return (
    <div className="space-y-2">
      {/* Stats row */}
      <div
        className={cn(
          'flex flex-wrap gap-4 text-green-600 dark:text-green-500',
          compact ? 'text-[10px]' : 'text-xs'
        )}
      >
        {metadata.row_count !== undefined && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 cursor-help">
                  <Table className={compact ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
                  <span>{metadata.row_count.toLocaleString()} rows</span>
                  {metadata.sampled && (
                    <Badge
                      variant="outline"
                      className="text-[8px] px-1 py-0 h-3 ml-1"
                    >
                      sampled
                    </Badge>
                  )}
                </div>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs">
                  {metadata.sampled
                    ? `Sampled from ${metadata.sample_size?.toLocaleString() || 'unknown'} rows`
                    : 'Total row count'}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}

        {metadata.column_count !== undefined && (
          <div className="flex items-center gap-1">
            <Database className={compact ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
            <span>{metadata.column_count} columns</span>
          </div>
        )}

        {latencyMs !== undefined && (
          <div className="flex items-center gap-1">
            <Clock className={compact ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
            <span>{latencyMs}ms</span>
          </div>
        )}

        {metadata.server_version && (
          <div className="flex items-center gap-1 text-muted-foreground">
            <Server className={compact ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
            <span>v{metadata.server_version}</span>
          </div>
        )}
      </div>

      {/* Server info */}
      {metadata.server_info && Object.keys(metadata.server_info).length > 0 && (
        <ServerInfoDisplay info={metadata.server_info} compact={compact} />
      )}

      {/* Capabilities badges */}
      {showCapabilities &&
        metadata.capabilities &&
        metadata.capabilities.length > 0 && (
          <SourceCapabilities
            capabilities={metadata.capabilities}
            size={compact ? 'xs' : 'sm'}
            colorScheme="success"
          />
        )}
    </div>
  )
}

// ============================================================================
// Server Info Display
// ============================================================================

interface ServerInfoDisplayProps {
  info: Record<string, unknown>
  compact?: boolean
}

function ServerInfoDisplay({ info, compact = false }: ServerInfoDisplayProps) {
  // Filter out null/undefined values and format for display
  const displayItems = Object.entries(info)
    .filter(([, value]) => value !== null && value !== undefined)
    .slice(0, 4) // Limit to 4 items

  if (displayItems.length === 0) return null

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              'flex items-center gap-1 text-muted-foreground cursor-help',
              compact ? 'text-[10px]' : 'text-xs'
            )}
          >
            <Info className={compact ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
            <span>Server info available</span>
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-[300px]">
          <div className="space-y-1">
            {displayItems.map(([key, value]) => (
              <div key={key} className="flex justify-between gap-4 text-xs">
                <span className="text-muted-foreground">{formatKey(key)}:</span>
                <span className="font-mono">{String(value)}</span>
              </div>
            ))}
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}

function formatKey(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

// ============================================================================
// Troubleshooting Hints
// ============================================================================

interface TroubleshootingHintsProps {
  error: string
  compact?: boolean
}

/**
 * Provides contextual troubleshooting hints based on common error patterns.
 */
function TroubleshootingHints({ error, compact = false }: TroubleshootingHintsProps) {
  const lowerError = error.toLowerCase()
  const hints: string[] = []

  // Connection refused / network errors
  if (
    lowerError.includes('connection refused') ||
    lowerError.includes('econnrefused') ||
    lowerError.includes('connect etimedout')
  ) {
    hints.push('Check that the server is running and accessible')
    hints.push('Verify the host and port are correct')
    hints.push('Check firewall settings')
  }

  // Authentication errors
  if (
    lowerError.includes('authentication') ||
    lowerError.includes('password') ||
    lowerError.includes('access denied') ||
    lowerError.includes('login') ||
    lowerError.includes('unauthorized')
  ) {
    hints.push('Verify your username and password')
    hints.push('Check that the user has necessary permissions')
    hints.push('For cloud warehouses, verify your API key or token')
  }

  // SSL/TLS errors
  if (
    lowerError.includes('ssl') ||
    lowerError.includes('certificate') ||
    lowerError.includes('tls')
  ) {
    hints.push('Check SSL/TLS settings')
    hints.push('Verify certificate configuration')
    hints.push('Try disabling SSL verification for testing (not recommended for production)')
  }

  // Database not found
  if (
    lowerError.includes('database') &&
    (lowerError.includes('not found') ||
      lowerError.includes('does not exist') ||
      lowerError.includes('unknown database'))
  ) {
    hints.push('Verify the database name is correct')
    hints.push('Check that the database exists')
    hints.push('Ensure the user has access to the database')
  }

  // Table not found
  if (
    lowerError.includes('table') &&
    (lowerError.includes('not found') ||
      lowerError.includes('does not exist') ||
      lowerError.includes('unknown'))
  ) {
    hints.push('Verify the table name is correct')
    hints.push('Check the schema name if applicable')
    hints.push('Ensure the user has SELECT permission on the table')
  }

  // File not found
  if (
    lowerError.includes('file not found') ||
    lowerError.includes('no such file') ||
    lowerError.includes('filenotfounderror')
  ) {
    hints.push('Check that the file path is correct')
    hints.push('Verify the file exists and is accessible')
    hints.push('Ensure the server has read permissions for the file')
  }

  // Timeout errors
  if (
    lowerError.includes('timeout') ||
    lowerError.includes('timed out')
  ) {
    hints.push('Check network connectivity')
    hints.push('The server might be under heavy load')
    hints.push('Consider increasing timeout settings')
  }

  // Cloud-specific errors
  if (lowerError.includes('bigquery')) {
    hints.push('Check your Google Cloud project ID')
    hints.push('Verify your service account credentials')
  }

  if (lowerError.includes('snowflake')) {
    hints.push('Verify your Snowflake account identifier')
    hints.push('Check warehouse and role settings')
  }

  if (lowerError.includes('redshift')) {
    hints.push('Ensure your cluster is available')
    hints.push('Check IAM role permissions if using IAM auth')
  }

  // Driver/dependency errors
  if (
    lowerError.includes('driver') ||
    lowerError.includes('module') ||
    lowerError.includes('import')
  ) {
    hints.push('Required database driver may not be installed')
    hints.push('Check the installation requirements for this data source')
  }

  if (hints.length === 0) return null

  return (
    <div className="mt-2 space-y-1">
      <div
        className={cn(
          'font-medium text-muted-foreground',
          compact ? 'text-[10px]' : 'text-xs'
        )}
      >
        Troubleshooting tips:
      </div>
      <ul
        className={cn(
          'list-inside list-disc space-y-0.5 text-muted-foreground',
          compact ? 'text-[10px]' : 'text-xs'
        )}
      >
        {hints.slice(0, 4).map((hint, index) => (
          <li key={index}>{hint}</li>
        ))}
      </ul>
    </div>
  )
}

// ============================================================================
// Exports
// ============================================================================

export { TroubleshootingHints }
// Note: ConnectionTestResultData is already exported at definition (line 45)
export default ConnectionTestResult
