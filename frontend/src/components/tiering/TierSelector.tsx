/**
 * TierSelector - Select a storage tier from available options.
 */

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Database, Thermometer, Snowflake, Archive } from 'lucide-react'
import type { StorageTier, TierType } from '@/api/modules/tiering'

const TIER_ICONS: Record<TierType, typeof Database> = {
  hot: Thermometer,
  warm: Database,
  cold: Snowflake,
  archive: Archive,
}

const TIER_COLORS: Record<TierType, string> = {
  hot: 'bg-red-500/10 text-red-500',
  warm: 'bg-orange-500/10 text-orange-500',
  cold: 'bg-blue-500/10 text-blue-500',
  archive: 'bg-gray-500/10 text-gray-500',
}

interface TierSelectorProps {
  tiers: StorageTier[]
  value: string | undefined
  onChange: (tierId: string) => void
  placeholder?: string
  disabled?: boolean
  excludeId?: string // Exclude a tier by ID (e.g., when selecting destination tier)
}

export function TierSelector({
  tiers,
  value,
  onChange,
  placeholder = 'Select a tier',
  disabled = false,
  excludeId,
}: TierSelectorProps) {
  const availableTiers = excludeId
    ? tiers.filter((t) => t.id !== excludeId)
    : tiers

  const selectedTier = tiers.find((t) => t.id === value)

  return (
    <Select value={value} onValueChange={onChange} disabled={disabled}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder}>
          {selectedTier && (
            <div className="flex items-center gap-2">
              {(() => {
                const Icon = TIER_ICONS[selectedTier.tier_type]
                return <Icon className="h-4 w-4" />
              })()}
              <span>{selectedTier.name}</span>
              <Badge
                variant="secondary"
                className={`ml-1 text-xs ${TIER_COLORS[selectedTier.tier_type]}`}
              >
                {selectedTier.tier_type}
              </Badge>
            </div>
          )}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {availableTiers.length === 0 ? (
          <div className="py-2 px-3 text-sm text-muted-foreground">
            No tiers available
          </div>
        ) : (
          availableTiers.map((tier) => {
            const Icon = TIER_ICONS[tier.tier_type]
            return (
              <SelectItem key={tier.id} value={tier.id}>
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  <span>{tier.name}</span>
                  <Badge
                    variant="secondary"
                    className={`ml-1 text-xs ${TIER_COLORS[tier.tier_type]}`}
                  >
                    {tier.tier_type}
                  </Badge>
                  {!tier.is_active && (
                    <Badge variant="outline" className="ml-1 text-xs">
                      Inactive
                    </Badge>
                  )}
                </div>
              </SelectItem>
            )
          })
        )}
      </SelectContent>
    </Select>
  )
}

export { TIER_ICONS, TIER_COLORS }
