/**
 * PolicyConfigForm - Dynamic form for policy-specific configuration.
 */

import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type {
  TierPolicyType,
  PolicyConfig,
  AgeBasedPolicyConfig,
  AccessBasedPolicyConfig,
  SizeBasedPolicyConfig,
  ScheduledPolicyConfig,
  CompositePolicyConfig,
  CustomPolicyConfig,
} from '@/api/modules/tiering'

interface PolicyConfigFormProps {
  policyType: TierPolicyType
  config: PolicyConfig
  onChange: (config: PolicyConfig) => void
}

const DAYS_OF_WEEK = [
  { value: 0, label: 'Monday' },
  { value: 1, label: 'Tuesday' },
  { value: 2, label: 'Wednesday' },
  { value: 3, label: 'Thursday' },
  { value: 4, label: 'Friday' },
  { value: 5, label: 'Saturday' },
  { value: 6, label: 'Sunday' },
]

export function PolicyConfigForm({
  policyType,
  config,
  onChange,
}: PolicyConfigFormProps) {
  switch (policyType) {
    case 'age_based':
      return (
        <AgeBasedConfigForm
          config={config as AgeBasedPolicyConfig}
          onChange={onChange}
        />
      )
    case 'access_based':
      return (
        <AccessBasedConfigForm
          config={config as AccessBasedPolicyConfig}
          onChange={onChange}
        />
      )
    case 'size_based':
      return (
        <SizeBasedConfigForm
          config={config as SizeBasedPolicyConfig}
          onChange={onChange}
        />
      )
    case 'scheduled':
      return (
        <ScheduledConfigForm
          config={config as ScheduledPolicyConfig}
          onChange={onChange}
        />
      )
    case 'composite':
      return (
        <CompositeConfigForm
          config={config as CompositePolicyConfig}
          onChange={onChange}
        />
      )
    case 'custom':
      return (
        <CustomConfigForm
          config={config as CustomPolicyConfig}
          onChange={onChange}
        />
      )
    default:
      return <div className="text-muted-foreground text-sm">Unknown policy type</div>
  }
}

function AgeBasedConfigForm({
  config,
  onChange,
}: {
  config: AgeBasedPolicyConfig
  onChange: (config: PolicyConfig) => void
}) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="after_days">After Days</Label>
          <Input
            id="after_days"
            type="number"
            min={0}
            max={3650}
            value={config.after_days || ''}
            onChange={(e) =>
              onChange({
                ...config,
                after_days: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
          <p className="text-xs text-muted-foreground">
            Days since creation before migration
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="after_hours">After Hours</Label>
          <Input
            id="after_hours"
            type="number"
            min={0}
            max={23}
            value={config.after_hours || ''}
            onChange={(e) =>
              onChange({
                ...config,
                after_hours: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
          <p className="text-xs text-muted-foreground">
            Additional hours (combined with days)
          </p>
        </div>
      </div>
    </div>
  )
}

function AccessBasedConfigForm({
  config,
  onChange,
}: {
  config: AccessBasedPolicyConfig
  onChange: (config: PolicyConfig) => void
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="inactive_days">Inactive Days (for demotion)</Label>
        <Input
          id="inactive_days"
          type="number"
          min={1}
          max={3650}
          value={config.inactive_days || ''}
          onChange={(e) =>
            onChange({
              ...config,
              inactive_days: e.target.value ? parseInt(e.target.value) : undefined,
            })
          }
          placeholder="30"
        />
        <p className="text-xs text-muted-foreground">
          Days without access to trigger demotion
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="min_access_count">Min Access Count (for promotion)</Label>
          <Input
            id="min_access_count"
            type="number"
            min={1}
            max={1000000}
            value={config.min_access_count || ''}
            onChange={(e) =>
              onChange({
                ...config,
                min_access_count: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="100"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="access_window_days">Access Window (days)</Label>
          <Input
            id="access_window_days"
            type="number"
            min={1}
            max={365}
            value={config.access_window_days || 7}
            onChange={(e) =>
              onChange({
                ...config,
                access_window_days: parseInt(e.target.value) || 7,
              })
            }
            placeholder="7"
          />
        </div>
      </div>
    </div>
  )
}

function SizeBasedConfigForm({
  config,
  onChange,
}: {
  config: SizeBasedPolicyConfig
  onChange: (config: PolicyConfig) => void
}) {
  return (
    <div className="space-y-4">
      <div className="text-sm font-medium">Item Size Threshold</div>
      <div className="grid grid-cols-4 gap-4">
        <div className="space-y-2">
          <Label htmlFor="min_size_bytes">Bytes</Label>
          <Input
            id="min_size_bytes"
            type="number"
            min={0}
            value={config.min_size_bytes || ''}
            onChange={(e) =>
              onChange({
                ...config,
                min_size_bytes: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="min_size_kb">KB</Label>
          <Input
            id="min_size_kb"
            type="number"
            min={0}
            value={config.min_size_kb || ''}
            onChange={(e) =>
              onChange({
                ...config,
                min_size_kb: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="min_size_mb">MB</Label>
          <Input
            id="min_size_mb"
            type="number"
            min={0}
            value={config.min_size_mb || ''}
            onChange={(e) =>
              onChange({
                ...config,
                min_size_mb: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="min_size_gb">GB</Label>
          <Input
            id="min_size_gb"
            type="number"
            min={0}
            value={config.min_size_gb || ''}
            onChange={(e) =>
              onChange({
                ...config,
                min_size_gb: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
        </div>
      </div>
      <div className="text-sm font-medium">Tier Capacity Limit</div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="tier_max_size_bytes">Max Tier Size (bytes)</Label>
          <Input
            id="tier_max_size_bytes"
            type="number"
            min={0}
            value={config.tier_max_size_bytes || ''}
            onChange={(e) =>
              onChange({
                ...config,
                tier_max_size_bytes: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="tier_max_size_gb">Max Tier Size (GB)</Label>
          <Input
            id="tier_max_size_gb"
            type="number"
            min={0}
            value={config.tier_max_size_gb || ''}
            onChange={(e) =>
              onChange({
                ...config,
                tier_max_size_gb: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
        </div>
      </div>
    </div>
  )
}

function ScheduledConfigForm({
  config,
  onChange,
}: {
  config: ScheduledPolicyConfig
  onChange: (config: PolicyConfig) => void
}) {
  const selectedDays = config.on_days || []

  const toggleDay = (day: number) => {
    const newDays = selectedDays.includes(day)
      ? selectedDays.filter((d) => d !== day)
      : [...selectedDays, day].sort()
    onChange({ ...config, on_days: newDays.length > 0 ? newDays : undefined })
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Days of Week</Label>
        <div className="flex flex-wrap gap-2">
          {DAYS_OF_WEEK.map(({ value, label }) => (
            <label
              key={value}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md border cursor-pointer transition-colors ${
                selectedDays.includes(value)
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-background hover:bg-muted'
              }`}
            >
              <Checkbox
                checked={selectedDays.includes(value)}
                onCheckedChange={() => toggleDay(value)}
                className="sr-only"
              />
              <span className="text-sm">{label.slice(0, 3)}</span>
            </label>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">
          Leave empty for every day
        </p>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="at_hour">At Hour (0-23)</Label>
          <Select
            value={config.at_hour?.toString() || ''}
            onValueChange={(v) =>
              onChange({
                ...config,
                at_hour: v ? parseInt(v) : undefined,
              })
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Any hour" />
            </SelectTrigger>
            <SelectContent>
              {Array.from({ length: 24 }, (_, i) => (
                <SelectItem key={i} value={i.toString()}>
                  {i.toString().padStart(2, '0')}:00
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label htmlFor="min_age_days">Min Age (days)</Label>
          <Input
            id="min_age_days"
            type="number"
            min={0}
            max={3650}
            value={config.min_age_days || ''}
            onChange={(e) =>
              onChange({
                ...config,
                min_age_days: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            placeholder="0"
          />
        </div>
      </div>
    </div>
  )
}

function CompositeConfigForm({
  config,
  onChange,
}: {
  config: CompositePolicyConfig
  onChange: (config: PolicyConfig) => void
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Combination Logic</Label>
        <div className="flex gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="require_all"
              checked={config.require_all !== false}
              onChange={() => onChange({ ...config, require_all: true })}
              className="h-4 w-4"
            />
            <div>
              <div className="font-medium">AND (All must match)</div>
              <div className="text-xs text-muted-foreground">
                All child policies must match for migration
              </div>
            </div>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="require_all"
              checked={config.require_all === false}
              onChange={() => onChange({ ...config, require_all: false })}
              className="h-4 w-4"
            />
            <div>
              <div className="font-medium">OR (Any can match)</div>
              <div className="text-xs text-muted-foreground">
                Any child policy match triggers migration
              </div>
            </div>
          </label>
        </div>
      </div>
      <div className="p-3 bg-muted/50 rounded-md text-sm">
        <strong>Note:</strong> Child policies are managed separately after creation.
        Create child policies and assign them to this composite policy.
      </div>
    </div>
  )
}

function CustomConfigForm({
  config,
  onChange,
}: {
  config: CustomPolicyConfig
  onChange: (config: PolicyConfig) => void
}) {
  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="predicate_expression">Predicate Expression</Label>
        <Textarea
          id="predicate_expression"
          value={config.predicate_expression || ''}
          onChange={(e) =>
            onChange({ ...config, predicate_expression: e.target.value })
          }
          placeholder="info.size_bytes > 1024 * 1024 and info.access_count < 5"
          rows={4}
          className="font-mono text-sm"
        />
        <p className="text-xs text-muted-foreground">
          Python expression that receives TierInfo object as 'info'. Must return boolean.
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="custom_description">Description</Label>
        <Input
          id="custom_description"
          value={config.description || ''}
          onChange={(e) => onChange({ ...config, description: e.target.value })}
          placeholder="Large but rarely accessed items"
        />
      </div>
      <div className="p-3 bg-muted/50 rounded-md text-sm">
        <strong>Available properties:</strong>
        <ul className="mt-1 ml-4 list-disc text-muted-foreground">
          <li>info.item_id - Item identifier</li>
          <li>info.tier_name - Current tier name</li>
          <li>info.created_at - Creation datetime</li>
          <li>info.access_count - Number of accesses</li>
          <li>info.last_accessed - Last access datetime</li>
          <li>info.size_bytes - Item size in bytes</li>
        </ul>
      </div>
    </div>
  )
}
