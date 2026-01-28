/**
 * Storage Tiering Page.
 *
 * Manages storage tiers, policies, configurations, and migration history.
 * Supports composite policies with AND/OR logic (truthound 1.2.10+).
 */

import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { Database } from 'lucide-react'
import { StorageTieringTab } from '@/components/tiering'

export default function StorageTiering() {
  const t = useSafeIntlayer('tiering')

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Database className="h-6 w-6 text-primary" />
            {t.title}
          </h1>
          <p className="text-muted-foreground">
            {t.description}
          </p>
        </div>
      </div>

      {/* Main Content */}
      <StorageTieringTab />
    </div>
  )
}
