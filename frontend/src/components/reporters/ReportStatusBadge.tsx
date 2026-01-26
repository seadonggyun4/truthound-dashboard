/**
 * ReportStatusBadge - Status indicator for reports.
 *
 * Displays report status with appropriate color and icon.
 */

import { Clock, RefreshCw, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { ReportStatus } from '@/types/reporters'
import { getStatusVariant } from '@/types/reporters'

interface ReportStatusBadgeProps {
  status: ReportStatus
  showLabel?: boolean
  className?: string
}

const statusConfig: Record<
  ReportStatus,
  {
    icon: React.ComponentType<{ className?: string }>
    label: string
    animateIcon?: boolean
  }
> = {
  pending: {
    icon: Clock,
    label: 'Pending',
  },
  generating: {
    icon: RefreshCw,
    label: 'Generating',
    animateIcon: true,
  },
  completed: {
    icon: CheckCircle,
    label: 'Completed',
  },
  failed: {
    icon: XCircle,
    label: 'Failed',
  },
  expired: {
    icon: AlertCircle,
    label: 'Expired',
  },
}

export function ReportStatusBadge({
  status,
  showLabel = true,
  className,
}: ReportStatusBadgeProps) {
  const config = statusConfig[status]
  const Icon = config.icon
  const variant = getStatusVariant(status)

  return (
    <Badge variant={variant} className={`flex items-center gap-1 ${className ?? ''}`}>
      <Icon className={`h-3 w-3 ${config.animateIcon ? 'animate-spin' : ''}`} />
      {showLabel && <span>{config.label}</span>}
    </Badge>
  )
}
