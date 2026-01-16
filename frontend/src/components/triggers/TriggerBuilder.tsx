/**
 * TriggerBuilder - Main component for configuring schedule triggers.
 *
 * Provides a unified interface for configuring all trigger types:
 * - Cron: Traditional cron expressions
 * - Interval: Fixed time intervals
 * - DataChange: Profile-based change detection
 * - Composite: Combine multiple triggers
 * - Event: Respond to system events
 * - Manual: API-only execution
 */

import { useState, useCallback, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TriggerTypeSelector } from './TriggerTypeSelector'
import { CronTriggerForm } from './CronTriggerForm'
import { IntervalTriggerForm } from './IntervalTriggerForm'
import { DataChangeTriggerForm } from './DataChangeTriggerForm'
import { CompositeTriggerForm } from './CompositeTriggerForm'
import { TriggerPreview } from './TriggerPreview'
import { Clock, Timer, TrendingUp, Layers, Zap, Hand } from 'lucide-react'

export type TriggerType = 'cron' | 'interval' | 'data_change' | 'composite' | 'event' | 'manual'

export interface TriggerConfig {
  type: TriggerType
  // Cron specific
  expression?: string
  timezone?: string
  // Interval specific
  seconds?: number
  minutes?: number
  hours?: number
  days?: number
  // Data change specific
  change_threshold?: number
  metrics?: string[]
  check_interval_minutes?: number
  // Composite specific
  operator?: 'and' | 'or'
  triggers?: TriggerConfig[]
  // Event specific
  event_types?: string[]
  source_filter?: string[]
}

interface TriggerBuilderProps {
  value: TriggerConfig
  onChange: (config: TriggerConfig) => void
  /** Legacy cron expression for backward compatibility */
  legacyCronExpression?: string
  /** Show compact mode (less spacing) */
  compact?: boolean
}

const TRIGGER_TYPE_INFO: Record<TriggerType, {
  icon: React.ComponentType<{ className?: string }>
  label: string
  description: string
}> = {
  cron: {
    icon: Clock,
    label: 'Cron Schedule',
    description: 'Schedule using cron expressions (e.g., daily at midnight)',
  },
  interval: {
    icon: Timer,
    label: 'Interval',
    description: 'Run at fixed time intervals (e.g., every 6 hours)',
  },
  data_change: {
    icon: TrendingUp,
    label: 'Data Change',
    description: 'Trigger when data profile changes by a threshold percentage',
  },
  composite: {
    icon: Layers,
    label: 'Composite',
    description: 'Combine multiple triggers with AND/OR logic',
  },
  event: {
    icon: Zap,
    label: 'Event',
    description: 'Trigger in response to system events (e.g., schema changes)',
  },
  manual: {
    icon: Hand,
    label: 'Manual',
    description: 'Only run when manually triggered via API',
  },
}

export function TriggerBuilder({
  value,
  onChange,
  legacyCronExpression,
  compact = false,
}: TriggerBuilderProps) {
  const [triggerType, setTriggerType] = useState<TriggerType>(value.type || 'cron')

  // Initialize from legacy cron expression if no type is set
  useEffect(() => {
    if (!value.type && legacyCronExpression) {
      onChange({
        type: 'cron',
        expression: legacyCronExpression,
      })
    }
  }, [legacyCronExpression, value.type, onChange])

  const handleTypeChange = useCallback((newType: TriggerType) => {
    setTriggerType(newType)

    // Create default config for new type
    const defaultConfigs: Record<TriggerType, TriggerConfig> = {
      cron: { type: 'cron', expression: '0 0 * * *' },
      interval: { type: 'interval', hours: 1 },
      data_change: {
        type: 'data_change',
        change_threshold: 0.05,
        metrics: ['row_count', 'null_percentage', 'distinct_count'],
        check_interval_minutes: 60,
      },
      composite: {
        type: 'composite',
        operator: 'and',
        triggers: [
          { type: 'cron', expression: '0 0 * * *' },
          { type: 'data_change', change_threshold: 0.05 },
        ],
      },
      event: {
        type: 'event',
        event_types: ['schema_changed'],
      },
      manual: { type: 'manual' },
    }

    onChange(defaultConfigs[newType])
  }, [onChange])

  const handleConfigChange = useCallback((updates: Partial<TriggerConfig>) => {
    onChange({ ...value, ...updates })
  }, [value, onChange])

  const typeInfo = TRIGGER_TYPE_INFO[triggerType]
  const TypeIcon = typeInfo.icon

  return (
    <div className={compact ? 'space-y-3' : 'space-y-4'}>
      {/* Trigger Type Selector */}
      <TriggerTypeSelector
        value={triggerType}
        onChange={handleTypeChange}
        compact={compact}
      />

      {/* Type-specific Configuration */}
      <Card>
        <CardHeader className={compact ? 'pb-2' : undefined}>
          <CardTitle className="text-base flex items-center gap-2">
            <TypeIcon className="h-4 w-4" />
            {typeInfo.label} Configuration
          </CardTitle>
          <CardDescription>{typeInfo.description}</CardDescription>
        </CardHeader>
        <CardContent>
          {triggerType === 'cron' && (
            <CronTriggerForm
              expression={value.expression || '0 0 * * *'}
              timezone={value.timezone}
              onChange={(expression, timezone) =>
                handleConfigChange({ expression, timezone })
              }
            />
          )}

          {triggerType === 'interval' && (
            <IntervalTriggerForm
              seconds={value.seconds}
              minutes={value.minutes}
              hours={value.hours}
              days={value.days}
              onChange={(interval) => handleConfigChange(interval)}
            />
          )}

          {triggerType === 'data_change' && (
            <DataChangeTriggerForm
              changeThreshold={value.change_threshold || 0.05}
              metrics={value.metrics || ['row_count', 'null_percentage', 'distinct_count']}
              checkIntervalMinutes={value.check_interval_minutes || 60}
              onChange={(config) =>
                handleConfigChange({
                  change_threshold: config.changeThreshold,
                  metrics: config.metrics,
                  check_interval_minutes: config.checkIntervalMinutes,
                })
              }
            />
          )}

          {triggerType === 'composite' && (
            <CompositeTriggerForm
              operator={value.operator || 'and'}
              triggers={value.triggers || []}
              onChange={(operator, triggers) =>
                handleConfigChange({ operator, triggers })
              }
            />
          )}

          {triggerType === 'event' && (
            <EventTriggerForm
              eventTypes={value.event_types || []}
              onChange={(event_types) => handleConfigChange({ event_types })}
            />
          )}

          {triggerType === 'manual' && (
            <div className="text-sm text-muted-foreground py-4 text-center">
              Manual triggers only execute when explicitly invoked via the API or "Run Now" button.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Preview */}
      <TriggerPreview config={value} />
    </div>
  )
}

// Event Trigger Form (inline since it's simple)
function EventTriggerForm({
  eventTypes,
  onChange,
}: {
  eventTypes: string[]
  onChange: (eventTypes: string[]) => void
}) {
  const AVAILABLE_EVENTS = [
    { value: 'validation_completed', label: 'Validation Completed' },
    { value: 'validation_failed', label: 'Validation Failed' },
    { value: 'schema_changed', label: 'Schema Changed' },
    { value: 'drift_detected', label: 'Drift Detected' },
    { value: 'profile_updated', label: 'Profile Updated' },
    { value: 'source_created', label: 'Source Created' },
    { value: 'source_updated', label: 'Source Updated' },
  ]

  const toggleEvent = (event: string) => {
    if (eventTypes.includes(event)) {
      onChange(eventTypes.filter((e) => e !== event))
    } else {
      onChange([...eventTypes, event])
    }
  }

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium">Trigger on Events:</label>
      <div className="grid grid-cols-2 gap-2">
        {AVAILABLE_EVENTS.map((event) => (
          <label
            key={event.value}
            className="flex items-center gap-2 p-2 border rounded cursor-pointer hover:bg-muted/50"
          >
            <input
              type="checkbox"
              checked={eventTypes.includes(event.value)}
              onChange={() => toggleEvent(event.value)}
              className="rounded"
            />
            <span className="text-sm">{event.label}</span>
          </label>
        ))}
      </div>
      {eventTypes.length === 0 && (
        <p className="text-sm text-amber-600">Select at least one event type</p>
      )}
    </div>
  )
}
