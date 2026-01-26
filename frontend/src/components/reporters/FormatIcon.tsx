/**
 * FormatIcon - Icon component for report formats.
 *
 * Displays appropriate icon based on report format type.
 */

import {
  FileCode,
  Braces,
  FileSpreadsheet,
  FileText,
  File,
  TestTube,
  FileJson2,
  Sheet,
  Terminal,
  Table,
} from 'lucide-react'
import type { ReportFormatType } from '@/types/reporters'

interface FormatIconProps {
  format: ReportFormatType
  className?: string
}

const formatIcons: Record<ReportFormatType, React.ComponentType<{ className?: string }>> = {
  html: FileCode,
  json: Braces,
  csv: FileSpreadsheet,
  markdown: FileText,
  pdf: File,
  junit: TestTube,
  yaml: FileJson2,
  ndjson: FileJson2,
  excel: Sheet,
  console: Terminal,
  table: Table,
}

export function FormatIcon({ format, className = 'h-4 w-4' }: FormatIconProps) {
  const Icon = formatIcons[format] || FileText
  return <Icon className={className} />
}
