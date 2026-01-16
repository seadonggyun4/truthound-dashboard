/**
 * EscalationLevelBuilder - Configure escalation levels and targets.
 *
 * Provides UI for building multi-level escalation policies with:
 * - Multiple escalation levels
 * - Targets per level (user, group, oncall, channel)
 * - Delay configuration
 */

import { useCallback } from 'react'
import { Plus, Trash2, GripVertical, User, Users, PhoneCall, Hash, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

export type TargetType = 'user' | 'group' | 'oncall' | 'channel'

export interface EscalationTarget {
  type: TargetType
  id: string
  name?: string
}

export interface EscalationLevel {
  level: number
  delay_minutes: number
  targets: EscalationTarget[]
}

interface EscalationLevelBuilderProps {
  levels: EscalationLevel[]
  onChange: (levels: EscalationLevel[]) => void
  maxLevels?: number
}

const TARGET_ICONS: Record<TargetType, typeof User> = {
  user: User,
  group: Users,
  oncall: PhoneCall,
  channel: Hash,
}

const TARGET_LABELS: Record<TargetType, string> = {
  user: 'User',
  group: 'Group',
  oncall: 'On-Call',
  channel: 'Channel',
}

export function EscalationLevelBuilder({
  levels,
  onChange,
  maxLevels = 5,
}: EscalationLevelBuilderProps) {
  const handleAddLevel = useCallback(() => {
    if (levels.length >= maxLevels) return
    const newLevel: EscalationLevel = {
      level: levels.length + 1,
      delay_minutes: 15,
      targets: [],
    }
    onChange([...levels, newLevel])
  }, [levels, onChange, maxLevels])

  const handleRemoveLevel = useCallback(
    (index: number) => {
      const newLevels = levels
        .filter((_, i) => i !== index)
        .map((l, i) => ({ ...l, level: i + 1 }))
      onChange(newLevels)
    },
    [levels, onChange]
  )

  const handleLevelChange = useCallback(
    (index: number, updates: Partial<EscalationLevel>) => {
      const newLevels = [...levels]
      newLevels[index] = { ...newLevels[index], ...updates }
      onChange(newLevels)
    },
    [levels, onChange]
  )

  const handleAddTarget = useCallback(
    (levelIndex: number) => {
      const newLevels = [...levels]
      newLevels[levelIndex].targets.push({
        type: 'user',
        id: '',
      })
      onChange(newLevels)
    },
    [levels, onChange]
  )

  const handleRemoveTarget = useCallback(
    (levelIndex: number, targetIndex: number) => {
      const newLevels = [...levels]
      newLevels[levelIndex].targets = newLevels[levelIndex].targets.filter(
        (_, i) => i !== targetIndex
      )
      onChange(newLevels)
    },
    [levels, onChange]
  )

  const handleTargetChange = useCallback(
    (levelIndex: number, targetIndex: number, updates: Partial<EscalationTarget>) => {
      const newLevels = [...levels]
      newLevels[levelIndex].targets[targetIndex] = {
        ...newLevels[levelIndex].targets[targetIndex],
        ...updates,
      }
      onChange(newLevels)
    },
    [levels, onChange]
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label className="text-base font-medium">Escalation Levels</Label>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleAddLevel}
          disabled={levels.length >= maxLevels}
        >
          <Plus className="h-4 w-4 mr-1" />
          Add Level
        </Button>
      </div>

      {levels.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="py-8 text-center">
            <p className="text-sm text-muted-foreground mb-3">
              No escalation levels configured. Add at least one level.
            </p>
            <Button type="button" variant="outline" size="sm" onClick={handleAddLevel}>
              <Plus className="h-4 w-4 mr-1" />
              Add First Level
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {levels.map((level, levelIndex) => (
            <Card key={levelIndex} className="relative">
              <CardHeader className="py-3 px-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab" />
                    <CardTitle className="text-sm">
                      Level {level.level}
                    </CardTitle>
                    <Badge variant="outline" className="text-xs">
                      {level.targets.length} target{level.targets.length !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{level.delay_minutes}m delay</span>
                    </div>
                    {levels.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemoveLevel(levelIndex)}
                        className="h-6 w-6 p-0"
                      >
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="py-3 px-4 space-y-4">
                {/* Delay Configuration */}
                <div className="flex items-center gap-3">
                  <Label className="text-xs shrink-0 w-28">Escalation Delay:</Label>
                  <div className="flex items-center gap-2">
                    <Input
                      type="number"
                      min={1}
                      max={1440}
                      value={level.delay_minutes}
                      onChange={(e) =>
                        handleLevelChange(levelIndex, {
                          delay_minutes: parseInt(e.target.value) || 15,
                        })
                      }
                      className="h-8 w-20"
                    />
                    <span className="text-xs text-muted-foreground">minutes</span>
                  </div>
                  <div className="flex gap-1">
                    {[5, 15, 30, 60].map((m) => (
                      <Button
                        key={m}
                        type="button"
                        variant="ghost"
                        size="sm"
                        className={cn(
                          'h-6 px-2 text-xs',
                          level.delay_minutes === m && 'bg-muted'
                        )}
                        onClick={() => handleLevelChange(levelIndex, { delay_minutes: m })}
                      >
                        {m}m
                      </Button>
                    ))}
                  </div>
                </div>

                {/* Targets */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-xs">Notification Targets</Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleAddTarget(levelIndex)}
                      className="h-6 text-xs"
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      Add Target
                    </Button>
                  </div>

                  {level.targets.length === 0 ? (
                    <p className="text-xs text-muted-foreground text-center py-2">
                      No targets. Add users, groups, on-call, or channels.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {level.targets.map((target, targetIndex) => {
                        const Icon = TARGET_ICONS[target.type]
                        return (
                          <div
                            key={targetIndex}
                            className="flex items-center gap-2 p-2 bg-muted/50 rounded"
                          >
                            <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                            <Select
                              value={target.type}
                              onValueChange={(v) =>
                                handleTargetChange(levelIndex, targetIndex, {
                                  type: v as TargetType,
                                })
                              }
                            >
                              <SelectTrigger className="h-7 w-28">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {Object.entries(TARGET_LABELS).map(([type, label]) => (
                                  <SelectItem key={type} value={type}>
                                    {label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <Input
                              placeholder={
                                target.type === 'user'
                                  ? 'User ID or email'
                                  : target.type === 'group'
                                  ? 'Group ID or name'
                                  : target.type === 'oncall'
                                  ? 'On-call schedule ID'
                                  : 'Channel ID'
                              }
                              value={target.id}
                              onChange={(e) =>
                                handleTargetChange(levelIndex, targetIndex, {
                                  id: e.target.value,
                                })
                              }
                              className="h-7 flex-1"
                            />
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => handleRemoveTarget(levelIndex, targetIndex)}
                              className="h-6 w-6 p-0 shrink-0"
                            >
                              <Trash2 className="h-3 w-3 text-destructive" />
                            </Button>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Visual Flow Indicator */}
      {levels.length > 1 && (
        <Card className="bg-muted/50">
          <CardContent className="py-3 px-4">
            <p className="text-xs text-muted-foreground">
              <strong>Escalation Flow:</strong>{' '}
              {levels.map((l, i) => (
                <span key={i}>
                  Level {l.level} ({l.targets.length} target
                  {l.targets.length !== 1 ? 's' : ''})
                  {i < levels.length - 1 && (
                    <span className="mx-2 text-primary">
                      → {l.delay_minutes}m →
                    </span>
                  )}
                </span>
              ))}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

export default EscalationLevelBuilder
