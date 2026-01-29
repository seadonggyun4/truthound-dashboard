/**
 * Lineage page - Data lineage visualization with multiple renderer support.
 *
 * Supports React Flow (default), Cytoscape.js (performance), and Mermaid (export).
 * Includes performance optimizations for large graphs (500+ nodes).
 */

import { useCallback, useEffect, useState } from 'react'
import { useSafeIntlayer } from '@/hooks/useSafeIntlayer'
import { Loader2, BarChart3, Zap, AlertTriangle } from 'lucide-react'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'
import {
  LineageGraph,
  LineageToolbar,
  LineageNodeDetails,
  ImpactAnalysisPanel,
  OpenLineageExport,
  OpenLineageConfig,
  LineageRendererSelector,
  CytoscapeLineageGraph,
  MermaidLineageGraph,
  LineageExportPanel,
  AnomalyLegend,
  type LineageRenderer,
  type AnomalyStatusLevel,
} from '@/components/lineage'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { PERFORMANCE_THRESHOLDS } from '@/lib/lineage-performance'
import { useLineageStore } from '@/stores/lineageStore'
import {
  createLineageNode,
  deleteLineageNode,
  analyzeLineageImpact,
  type LineageNode,
  type ImpactAnalysisResponse,
} from '@/api/modules/lineage'

// Local storage key for renderer preference
const RENDERER_PREFERENCE_KEY = 'lineage-renderer-preference'

export default function Lineage() {
  const t = useSafeIntlayer('lineage')
  const { toast } = useToast()

  // Zustand store for lineage data (persists across navigation)
  const {
    lineageData,
    isLoading,
    fetchLineageData,
    addNode,
    removeNode,
  } = useLineageStore()

  // Local UI state
  const [selectedNode, setSelectedNode] = useState<LineageNode | null>(null)
  const [impactAnalysis, setImpactAnalysis] = useState<ImpactAnalysisResponse | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  // Renderer state - load from localStorage
  const [renderer, setRenderer] = useState<LineageRenderer>(() => {
    const saved = localStorage.getItem(RENDERER_PREFERENCE_KEY)
    return (saved as LineageRenderer) || 'reactflow'
  })

  // Performance mode state (undefined = auto, true/false = forced)
  const [forcePerformanceMode, setForcePerformanceMode] = useState<boolean | undefined>(undefined)

  // Anomaly overlay state
  const [showAnomalyOverlay, setShowAnomalyOverlay] = useState(false)
  const [showAnomalyLegend, setShowAnomalyLegend] = useState(true)
  const [showImpactPaths, setShowImpactPaths] = useState(true)
  const [anomalyStatusFilter, setAnomalyStatusFilter] = useState<AnomalyStatusLevel[]>([
    'unknown', 'clean', 'low', 'medium', 'high'
  ])

  // Check if graph is large enough to warrant performance warning
  const isLargeGraph = (lineageData?.total_nodes ?? 0) >= PERFORMANCE_THRESHOLDS.WARNING_THRESHOLD

  // Save renderer preference to localStorage
  const handleRendererChange = useCallback(
    (newRenderer: LineageRenderer) => {
      setRenderer(newRenderer)
      localStorage.setItem(RENDERER_PREFERENCE_KEY, newRenderer)
      toast({ title: str(t.savedRendererPreference) })
    },
    [] // eslint-disable-line react-hooks/exhaustive-deps
  )

  // Handle manual performance mode toggle
  const handleForcePerformanceMode = useCallback((checked: boolean) => {
    setForcePerformanceMode(checked ? true : undefined)
  }, [])

  // Load lineage data on mount (uses cached data if available)
  useEffect(() => {
    fetchLineageData()
  }, [fetchLineageData])

  // Force refresh handler
  const handleRefresh = useCallback(() => {
    fetchLineageData(true)
  }, [fetchLineageData])

  // Handle node selection
  const handleNodeClick = useCallback(
    (node: LineageNode) => {
      setSelectedNode(node)
      setImpactAnalysis(null)
    },
    []
  )

  // Handle add node
  const handleAddNode = useCallback(
    async (name: string, nodeType: LineageNode['node_type']) => {
      try {
        const newNode = await createLineageNode({
          name,
          node_type: nodeType,
        })

        // Optimistic update via store
        addNode(newNode)

        toast({ title: str(t.nodeCreated) })
      } catch (error) {
        toast({
          title: str(t.errorCreatingNode),
          variant: 'destructive',
        })
      }
    },
    [addNode] // eslint-disable-line react-hooks/exhaustive-deps
  )

  // Handle delete node
  const handleDeleteNode = useCallback(
    async (nodeId: string) => {
      try {
        await deleteLineageNode(nodeId)

        // Optimistic update via store
        removeNode(nodeId)
        setSelectedNode(null)

        toast({ title: str(t.nodeDeleted) })
      } catch (error) {
        toast({
          title: str(t.errorDeletingNode),
          variant: 'destructive',
        })
      }
    },
    [removeNode] // eslint-disable-line react-hooks/exhaustive-deps
  )

  // Handle impact analysis
  const handleAnalyzeImpact = useCallback(
    async (nodeId: string) => {
      setIsAnalyzing(true)
      try {
        const analysis = await analyzeLineageImpact(nodeId)
        setImpactAnalysis(analysis)
      } catch (error) {
        toast({
          title: 'Failed to analyze impact',
          variant: 'destructive',
        })
      } finally {
        setIsAnalyzing(false)
      }
    },
    [toast]
  )

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-[600px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Empty state
  if (lineageData && lineageData.nodes.length === 0) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{t.title}</h1>
            <p className="text-muted-foreground">{t.subtitle}</p>
          </div>
          <div className="flex items-center gap-2">
            <LineageRendererSelector value={renderer} onChange={handleRendererChange} />
            <OpenLineageConfig />
            <OpenLineageExport />
          </div>
        </div>

        <div className="flex h-[500px] flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed">
          <p className="text-lg font-medium">{t.noLineageYet}</p>
          <p className="text-muted-foreground">{t.noLineageDesc}</p>
          <LineageToolbar
            onAddNode={handleAddNode}
            onSavePositions={() => {}}
            onRefresh={handleRefresh}
            isSaving={false}
          />
        </div>
      </div>
    )
  }

  return (
    <TooltipProvider>
      <div className="p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-2xl font-bold">{t.title}</h1>
              <p className="text-muted-foreground">{t.subtitle}</p>
            </div>
            {/* Large graph indicator */}
            {isLargeGraph && (
              <Badge variant="secondary" className="text-xs">
                {lineageData?.total_nodes} nodes
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            {/* Anomaly overlay toggle */}
            <Button
              variant={showAnomalyOverlay ? 'default' : 'outline'}
              size="sm"
              onClick={() => setShowAnomalyOverlay(!showAnomalyOverlay)}
              className={showAnomalyOverlay ? 'bg-orange-500 hover:bg-orange-600' : ''}
            >
              <AlertTriangle className="mr-2 h-4 w-4" />
              {showAnomalyOverlay
                ? (t.anomaly?.hideAnomalies ?? 'Hide Anomalies')
                : (t.anomaly?.showAnomalies ?? 'Show Anomalies')}
            </Button>

            {/* Performance info popover */}
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm">
                  <BarChart3 className="mr-2 h-4 w-4" />
                  {str(t.performanceInfo)}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80">
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium">{str(t.performanceOptimizations)}</h4>
                    <p className="text-sm text-muted-foreground">
                      {str(t.performanceOptimizationsDesc)}
                    </p>
                  </div>

                  {/* Thresholds info */}
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>{str(t.clusteringThreshold)}</span>
                      <span className="font-mono">
                        {PERFORMANCE_THRESHOLDS.CLUSTERING_THRESHOLD} nodes
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>{str(t.virtualizationThreshold)}</span>
                      <span className="font-mono">
                        {PERFORMANCE_THRESHOLDS.VIRTUALIZATION_THRESHOLD} nodes
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>{str(t.warningThreshold)}</span>
                      <span className="font-mono">
                        {PERFORMANCE_THRESHOLDS.WARNING_THRESHOLD} nodes
                      </span>
                    </div>
                  </div>

                  {/* Manual override */}
                  <div className="flex items-center justify-between border-t pt-4">
                    <Label htmlFor="force-perf" className="flex items-center gap-2">
                      <Zap className="h-4 w-4" />
                      {str(t.forcePerformanceMode)}
                    </Label>
                    <Switch
                      id="force-perf"
                      checked={forcePerformanceMode ?? false}
                      onCheckedChange={handleForcePerformanceMode}
                    />
                  </div>
                </div>
              </PopoverContent>
            </Popover>

            <LineageRendererSelector value={renderer} onChange={handleRendererChange} />
            <LineageExportPanel
              nodes={lineageData?.nodes ?? []}
              edges={lineageData?.edges ?? []}
            />
            <OpenLineageConfig />
            <OpenLineageExport />
          </div>
        </div>

        {/* Main content area */}
        <div className="relative flex gap-4 h-[600px]">
          {/* Graph area */}
          <div className="flex-1 rounded-lg border overflow-hidden">
            {renderer === 'reactflow' && (
              <LineageGraph
                className="h-full"
                forcePerformanceMode={forcePerformanceMode}
              />
            )}

            {renderer === 'cytoscape' && lineageData && (
              <CytoscapeLineageGraph
                nodes={lineageData.nodes}
                edges={lineageData.edges}
                onNodeClick={handleNodeClick}
                className="h-full"
              />
            )}

            {renderer === 'mermaid' && lineageData && (
              <MermaidLineageGraph
                nodes={lineageData.nodes}
                edges={lineageData.edges}
                onNodeClick={handleNodeClick}
                className="h-full"
              />
            )}
          </div>

          {/* Side panel - show for cytoscape/mermaid */}
          {renderer !== 'reactflow' && (
            <div className="w-80 space-y-4 overflow-y-auto rounded-lg border p-4">
              <LineageNodeDetails
                node={selectedNode}
                edges={lineageData?.edges ?? []}
                allNodes={lineageData?.nodes ?? []}
                onDelete={handleDeleteNode}
                onAnalyzeImpact={handleAnalyzeImpact}
              />

              {impactAnalysis && (
                <ImpactAnalysisPanel
                  analysis={impactAnalysis}
                  isLoading={isAnalyzing}
                />
              )}
            </div>
          )}

          {/* Anomaly legend - floating panel when anomaly overlay is enabled */}
          {showAnomalyOverlay && (
            <div className="absolute bottom-4 left-4 z-10">
              <AnomalyLegend
                showLegend={showAnomalyLegend}
                onToggleLegend={() => setShowAnomalyLegend(!showAnomalyLegend)}
                selectedStatuses={anomalyStatusFilter}
                onStatusFilterChange={setAnomalyStatusFilter}
                showImpactPaths={showImpactPaths}
                onToggleImpactPaths={() => setShowImpactPaths(!showImpactPaths)}
              />
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  )
}
