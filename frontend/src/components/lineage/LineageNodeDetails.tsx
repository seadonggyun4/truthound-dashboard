/**
 * Side panel showing details of the selected lineage node.
 */

import { useIntlayer } from 'react-intlayer'
import {
  Database,
  ArrowRightLeft,
  Archive,
  ExternalLink,
  Calendar,
  Trash2,
  Edit2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { LineageNode as LineageNodeType, LineageEdge } from '@/api/modules/lineage'

interface LineageNodeDetailsProps {
  node: LineageNodeType | null
  edges: LineageEdge[]
  allNodes: LineageNodeType[]
  onEdit?: (node: LineageNodeType) => void
  onDelete?: (nodeId: string) => void
  onAnalyzeImpact?: (nodeId: string) => void
}

const nodeTypeConfig = {
  source: { icon: Database, color: 'text-blue-500', bgColor: 'bg-blue-500/10' },
  transform: { icon: ArrowRightLeft, color: 'text-amber-500', bgColor: 'bg-amber-500/10' },
  sink: { icon: Archive, color: 'text-green-500', bgColor: 'bg-green-500/10' },
}

export function LineageNodeDetails({
  node,
  edges,
  allNodes,
  onEdit,
  onDelete,
  onAnalyzeImpact,
}: LineageNodeDetailsProps) {
  const t = useIntlayer('lineage')

  if (!node) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-muted-foreground">
        <p>{t.noNodeSelected}</p>
      </div>
    )
  }

  const config = nodeTypeConfig[node.node_type]
  const Icon = config.icon

  // Find connected nodes
  const upstreamEdges = edges.filter((e) => e.target_node_id === node.id)
  const downstreamEdges = edges.filter((e) => e.source_node_id === node.id)

  const upstreamNodes = upstreamEdges
    .map((e) => allNodes.find((n) => n.id === e.source_node_id))
    .filter(Boolean) as LineageNodeType[]

  const downstreamNodes = downstreamEdges
    .map((e) => allNodes.find((n) => n.id === e.target_node_id))
    .filter(Boolean) as LineageNodeType[]

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={cn('rounded-lg p-2', config.bgColor)}>
            <Icon className={cn('h-5 w-5', config.color)} />
          </div>
          <div>
            <h3 className="font-semibold">{node.name}</h3>
            <Badge variant="outline" className="capitalize">
              {t.nodeTypes[node.node_type]}
            </Badge>
          </div>
        </div>

        <div className="flex gap-1">
          {onEdit && (
            <Button variant="ghost" size="icon" onClick={() => onEdit(node)}>
              <Edit2 className="h-4 w-4" />
            </Button>
          )}
          {onDelete && (
            <Button
              variant="ghost"
              size="icon"
              className="text-destructive"
              onClick={() => onDelete(node.id)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Linked source */}
      {node.source_id && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <ExternalLink className="h-4 w-4" />
          <span>{t.linkedSource}:</span>
          <Badge variant="secondary">{node.source_id.slice(0, 8)}...</Badge>
        </div>
      )}

      {/* Metadata */}
      {node.metadata && Object.keys(node.metadata).length > 0 && (
        <Card>
          <CardHeader className="py-3">
            <CardTitle className="text-sm">{t.metadata}</CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <div className="space-y-1 text-sm">
              {Object.entries(node.metadata).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-muted-foreground">{key}:</span>
                  <span className="font-medium">
                    {Array.isArray(value) ? value.join(', ') : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Connected nodes */}
      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-sm">{t.connectedNodes}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 py-2">
          {/* Upstream */}
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">
              {t.upstream} ({upstreamNodes.length})
            </p>
            {upstreamNodes.length === 0 ? (
              <p className="text-sm text-muted-foreground">None</p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {upstreamNodes.map((n) => (
                  <Badge key={n.id} variant="secondary" className="text-xs">
                    {n.name}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Downstream */}
          <div>
            <p className="mb-2 text-xs font-medium text-muted-foreground">
              {t.downstream} ({downstreamNodes.length})
            </p>
            {downstreamNodes.length === 0 ? (
              <p className="text-sm text-muted-foreground">None</p>
            ) : (
              <div className="flex flex-wrap gap-1">
                {downstreamNodes.map((n) => (
                  <Badge key={n.id} variant="secondary" className="text-xs">
                    {n.name}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Impact analysis button */}
      {onAnalyzeImpact && (
        <Button variant="outline" className="w-full" onClick={() => onAnalyzeImpact(node.id)}>
          {t.analyzeImpact}
        </Button>
      )}

      {/* Timestamps */}
      <div className="space-y-1 text-xs text-muted-foreground">
        <div className="flex items-center gap-2">
          <Calendar className="h-3 w-3" />
          <span>{t.createdAt}: {formatDate(node.created_at)}</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-3 w-3" />
          <span>{t.updatedAt}: {formatDate(node.updated_at)}</span>
        </div>
      </div>
    </div>
  )
}
