/**
 * Renderer selector dropdown for lineage visualization.
 *
 * Allows switching between different rendering engines:
 * - React Flow (default, interactive)
 * - Cytoscape (performance, large graphs)
 * - Mermaid (export, documentation)
 */

import { useSafeIntlayer as useIntlayer } from '@/hooks/useSafeIntlayer'
import { Monitor, Workflow, FileCode } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

/**
 * Available renderer types.
 */
export type LineageRenderer = 'reactflow' | 'cytoscape' | 'mermaid'

interface LineageRendererSelectorProps {
  value: LineageRenderer
  onChange: (renderer: LineageRenderer) => void
  className?: string
  disabled?: boolean
}

const rendererConfig: Record<
  LineageRenderer,
  { icon: typeof Monitor; label: string; description: string }
> = {
  reactflow: {
    icon: Workflow,
    label: 'React Flow',
    description: 'Interactive, drag & drop',
  },
  cytoscape: {
    icon: Monitor,
    label: 'Cytoscape',
    description: 'High performance, large graphs',
  },
  mermaid: {
    icon: FileCode,
    label: 'Mermaid',
    description: 'Export, documentation',
  },
}

export function LineageRendererSelector({
  value,
  onChange,
  className,
  disabled = false,
}: LineageRendererSelectorProps) {
  const t = useIntlayer('lineage')
  const currentConfig = rendererConfig[value]
  const CurrentIcon = currentConfig.icon

  return (
    <Select
      value={value}
      onValueChange={(v) => onChange(v as LineageRenderer)}
      disabled={disabled}
    >
      <SelectTrigger className={cn('w-[200px]', className)}>
        <div className="flex items-center gap-2">
          <CurrentIcon className="h-4 w-4 shrink-0" />
          <span className="truncate">{currentConfig.label}</span>
        </div>
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="reactflow" textValue="React Flow">
          <div className="flex items-center gap-2">
            <Workflow className="h-4 w-4 text-blue-500" />
            <div className="flex flex-col">
              <span>{t.renderers.reactflow}</span>
              <span className="text-xs text-muted-foreground">
                {rendererConfig.reactflow.description}
              </span>
            </div>
          </div>
        </SelectItem>
        <SelectItem value="cytoscape" textValue="Cytoscape">
          <div className="flex items-center gap-2">
            <Monitor className="h-4 w-4 text-green-500" />
            <div className="flex flex-col">
              <span>{t.renderers.cytoscape}</span>
              <span className="text-xs text-muted-foreground">
                {rendererConfig.cytoscape.description}
              </span>
            </div>
          </div>
        </SelectItem>
        <SelectItem value="mermaid" textValue="Mermaid">
          <div className="flex items-center gap-2">
            <FileCode className="h-4 w-4 text-purple-500" />
            <div className="flex flex-col">
              <span>{t.renderers.mermaid}</span>
              <span className="text-xs text-muted-foreground">
                {rendererConfig.mermaid.description}
              </span>
            </div>
          </div>
        </SelectItem>
      </SelectContent>
    </Select>
  )
}
