/**
 * Quality Reporter Page
 *
 * Comprehensive quality assessment and reporting for validation rules.
 * Features:
 * - Rule quality scoring (F1, precision, recall, accuracy)
 * - Quality level visualization (excellent, good, acceptable, poor, unacceptable)
 * - Report generation in multiple formats (HTML, JSON, Markdown, JUnit)
 * - Score filtering and comparison
 */
import { useState, useEffect, useCallback } from 'react'
import { useSafeIntlayer as useIntlayer } from '@/hooks/useSafeIntlayer'
import {
  Download,
  FileText,
  Filter,
  Play,
  RefreshCw,
  BarChart3,
  TrendingUp,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
} from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { useToast } from '@/hooks/use-toast'
import { str } from '@/lib/intlayer-utils'

import * as sourcesApi from '@/api/modules/sources'
import * as qualityApi from '@/api/modules/quality-reporter'

// ============================================================================
// Helper Components
// ============================================================================

function QualityLevelBadge({ level }: { level: qualityApi.QualityLevel }) {
  const content = useIntlayer('quality-reporter')

  const levelConfig: Record<
    qualityApi.QualityLevel,
    { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; className: string }
  > = {
    excellent: {
      label: str(content.levelExcellent),
      variant: 'default',
      className: 'bg-green-500 hover:bg-green-600',
    },
    good: {
      label: str(content.levelGood),
      variant: 'default',
      className: 'bg-blue-500 hover:bg-blue-600',
    },
    acceptable: {
      label: str(content.levelAcceptable),
      variant: 'secondary',
      className: 'bg-amber-500 hover:bg-amber-600 text-white',
    },
    poor: {
      label: str(content.levelPoor),
      variant: 'destructive',
      className: 'bg-red-500 hover:bg-red-600',
    },
    unacceptable: {
      label: str(content.levelUnacceptable),
      variant: 'destructive',
      className: 'bg-red-800 hover:bg-red-900',
    },
  }

  const config = levelConfig[level]

  return (
    <Badge variant={config.variant} className={config.className}>
      {config.label}
    </Badge>
  )
}

function MetricCard({
  label,
  value,
  description,
  icon: Icon,
}: {
  label: string
  value: number
  description?: string
  icon?: React.ElementType
}) {
  const percentage = (value * 100).toFixed(1)

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{label}</CardTitle>
        {Icon && <Icon className="h-4 w-4 text-muted-foreground" />}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{percentage}%</div>
        <Progress value={value * 100} className="mt-2" />
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  )
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string
  value: number | string
  icon?: React.ElementType
  color?: string
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{label}</CardTitle>
        {Icon && <Icon className={`h-4 w-4 ${color || 'text-muted-foreground'}`} />}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
      </CardContent>
    </Card>
  )
}

function LevelDistributionChart({
  distribution,
}: {
  distribution: qualityApi.QualityLevelDistribution[]
}) {
  const content = useIntlayer('quality-reporter')

  const levelLabels: Record<qualityApi.QualityLevel, string> = {
    excellent: str(content.levelExcellent),
    good: str(content.levelGood),
    acceptable: str(content.levelAcceptable),
    poor: str(content.levelPoor),
    unacceptable: str(content.levelUnacceptable),
  }

  const levelColors: Record<qualityApi.QualityLevel, string> = {
    excellent: 'bg-green-500',
    good: 'bg-blue-500',
    acceptable: 'bg-amber-500',
    poor: 'bg-red-500',
    unacceptable: 'bg-red-800',
  }

  return (
    <div className="space-y-3">
      {distribution.map((item) => (
        <div key={item.level} className="space-y-1">
          <div className="flex justify-between text-sm">
            <span>{levelLabels[item.level]}</span>
            <span className="text-muted-foreground">
              {item.count} ({item.percentage.toFixed(1)}%)
            </span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className={`h-full rounded-full ${levelColors[item.level]}`}
              style={{ width: `${item.percentage}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export default function QualityReporter() {
  const content = useIntlayer('quality-reporter')
  const common = useIntlayer('common')
  const { toast } = useToast()

  // State
  const [sources, setSources] = useState<sourcesApi.Source[]>([])
  const [selectedSourceId, setSelectedSourceId] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [scoring, setScoring] = useState(false)
  const [generating, setGenerating] = useState(false)

  const [scoreResult, setScoreResult] = useState<qualityApi.QualityScoreResponse | null>(null)
  const [summary, setSummary] = useState<qualityApi.QualitySummaryResponse | null>(null)
  const [reportPreview, setReportPreview] = useState<string | null>(null)

  // Configuration state
  const [sampleSize, setSampleSize] = useState(10000)
  const [reportFormat, setReportFormat] = useState<qualityApi.QualityReportFormat>('html')
  const [reportTheme, setReportTheme] = useState<'light' | 'dark' | 'professional'>('professional')
  const [includeCharts, setIncludeCharts] = useState(true)
  const [maxScores, setMaxScores] = useState<number | undefined>(undefined)

  // Preview dialog
  const [previewOpen, setPreviewOpen] = useState(false)

  // Load sources on mount
  useEffect(() => {
    loadSources()
  }, [])

  const loadSources = async () => {
    try {
      setLoading(true)
      const response = await sourcesApi.listSources()
      setSources(response.data)
    } catch (error) {
      toast({
        title: str(common.error),
        description: String(error),
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleScoreRules = useCallback(async () => {
    if (!selectedSourceId) {
      toast({
        title: str(common.error),
        description: str(content.noSourceSelected),
        variant: 'destructive',
      })
      return
    }

    try {
      setScoring(true)
      const result = await qualityApi.scoreSource(selectedSourceId, {
        sample_size: sampleSize,
      })
      setScoreResult(result)

      // Also get summary
      const summaryResult = await qualityApi.getQualitySummary(selectedSourceId, {
        sample_size: sampleSize,
      })
      setSummary(summaryResult)

      toast({
        title: str(common.success),
        description: str(content.scoreSuccess),
      })
    } catch (error) {
      toast({
        title: str(common.error),
        description: str(content.scoreFailed),
        variant: 'destructive',
      })
    } finally {
      setScoring(false)
    }
  }, [selectedSourceId, sampleSize, toast, common, content])

  const handleGenerateReport = useCallback(async () => {
    if (!selectedSourceId) {
      toast({
        title: str(common.error),
        description: str(content.noSourceSelected),
        variant: 'destructive',
      })
      return
    }

    try {
      setGenerating(true)
      const blob = await qualityApi.downloadQualityReport(selectedSourceId, {
        format: reportFormat,
        theme: reportTheme,
        include_charts: includeCharts,
        max_scores: maxScores,
      })

      // Create download link
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `quality_report.${reportFormat === 'junit' ? 'xml' : reportFormat}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      toast({
        title: str(common.success),
        description: str(content.downloadStarted),
      })
    } catch (error) {
      toast({
        title: str(common.error),
        description: str(content.downloadFailed),
        variant: 'destructive',
      })
    } finally {
      setGenerating(false)
    }
  }, [selectedSourceId, reportFormat, reportTheme, includeCharts, maxScores, toast, common, content])

  const handlePreviewReport = useCallback(async () => {
    if (!selectedSourceId) return

    try {
      setGenerating(true)
      const preview = await qualityApi.previewQualityReport(selectedSourceId, {
        format: 'html',
        theme: reportTheme,
        max_scores: maxScores || 20,
      })
      setReportPreview(preview)
      setPreviewOpen(true)
    } catch (error) {
      toast({
        title: str(common.error),
        description: str(content.reportFailed),
        variant: 'destructive',
      })
    } finally {
      setGenerating(false)
    }
  }, [selectedSourceId, reportTheme, maxScores, toast, common, content])

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">{content.pageTitle}</h1>
          <p className="text-muted-foreground mt-1">{content.pageDescription}</p>
        </div>
        <Button variant="outline" size="icon" onClick={loadSources} disabled={loading}>
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Source Selection and Actions */}
      <Card>
        <CardHeader>
          <CardTitle>{content.selectSource}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label>{content.sourceLabel}</Label>
              <Select value={selectedSourceId} onValueChange={setSelectedSourceId}>
                <SelectTrigger>
                  <SelectValue placeholder={str(content.sourcePlaceholder)} />
                </SelectTrigger>
                <SelectContent>
                  {sources.map((source) => (
                    <SelectItem key={source.id} value={source.id}>
                      {source.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>{content.sampleSizeLabel}</Label>
              <Input
                type="number"
                value={sampleSize}
                onChange={(e) => setSampleSize(Number(e.target.value))}
                min={100}
                max={1000000}
              />
            </div>

            <div className="flex items-end gap-2">
              <Button
                onClick={handleScoreRules}
                disabled={!selectedSourceId || scoring}
                className="flex-1"
              >
                {scoring ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                {content.scoreRules}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      {scoreResult ? (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">{content.tabOverview}</TabsTrigger>
            <TabsTrigger value="scores">{content.tabScores}</TabsTrigger>
            <TabsTrigger value="report">{content.tabReport}</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            {/* Statistics Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatCard
                label={str(content.totalRules)}
                value={scoreResult.statistics?.total_count || 0}
                icon={FileText}
              />
              <MetricCard
                label={str(content.averageF1)}
                value={scoreResult.statistics?.avg_f1 || 0}
                icon={BarChart3}
              />
              <StatCard
                label={str(content.shouldUse)}
                value={scoreResult.statistics?.should_use_count || 0}
                icon={CheckCircle}
                color="text-green-500"
              />
              <StatCard
                label={str(content.shouldNotUse)}
                value={
                  (scoreResult.statistics?.total_count || 0) -
                  (scoreResult.statistics?.should_use_count || 0)
                }
                icon={XCircle}
                color="text-red-500"
              />
            </div>

            {/* Metrics and Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Quality Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    {content.statistics}
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid grid-cols-2 gap-4">
                  <MetricCard
                    label={str(content.metricF1Score)}
                    value={scoreResult.statistics?.avg_f1 || 0}
                  />
                  <MetricCard
                    label={str(content.metricPrecision)}
                    value={scoreResult.statistics?.avg_precision || 0}
                  />
                  <MetricCard
                    label={str(content.metricRecall)}
                    value={scoreResult.statistics?.avg_recall || 0}
                  />
                  <MetricCard
                    label={str(content.metricConfidence)}
                    value={scoreResult.statistics?.avg_confidence || 0}
                  />
                </CardContent>
              </Card>

              {/* Level Distribution */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    {content.levelDistribution}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {scoreResult.level_distribution && (
                    <LevelDistributionChart distribution={scoreResult.level_distribution} />
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Scores Tab */}
          <TabsContent value="scores">
            <Card>
              <CardHeader>
                <CardTitle>{content.tabScores}</CardTitle>
                <CardDescription>
                  {scoreResult.scores.length} {str(content.totalRules).toLowerCase()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{content.ruleName}</TableHead>
                        <TableHead>{content.ruleType}</TableHead>
                        <TableHead>{content.column}</TableHead>
                        <TableHead>{content.qualityLevel}</TableHead>
                        <TableHead className="text-right">{content.metricF1Score}</TableHead>
                        <TableHead className="text-right">{content.metricPrecision}</TableHead>
                        <TableHead className="text-right">{content.metricRecall}</TableHead>
                        <TableHead className="text-center">{content.useRecommendation}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scoreResult.scores.map((score, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{score.rule_name}</TableCell>
                          <TableCell>{score.rule_type || '-'}</TableCell>
                          <TableCell>{score.column || '-'}</TableCell>
                          <TableCell>
                            <QualityLevelBadge level={score.metrics.quality_level} />
                          </TableCell>
                          <TableCell className="text-right">
                            {(score.metrics.f1_score * 100).toFixed(1)}%
                          </TableCell>
                          <TableCell className="text-right">
                            {(score.metrics.precision * 100).toFixed(1)}%
                          </TableCell>
                          <TableCell className="text-right">
                            {(score.metrics.recall * 100).toFixed(1)}%
                          </TableCell>
                          <TableCell className="text-center">
                            {score.should_use ? (
                              <CheckCircle className="h-5 w-5 text-green-500 mx-auto" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-500 mx-auto" />
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Report Tab */}
          <TabsContent value="report" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>{content.reportConfig}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Format */}
                  <div className="space-y-2">
                    <Label>{content.selectSource}</Label>
                    <Select
                      value={reportFormat}
                      onValueChange={(v) => setReportFormat(v as qualityApi.QualityReportFormat)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="html">{content.formatHtml}</SelectItem>
                        <SelectItem value="json">{content.formatJson}</SelectItem>
                        <SelectItem value="markdown">{content.formatMarkdown}</SelectItem>
                        <SelectItem value="console">{content.formatConsole}</SelectItem>
                        <SelectItem value="junit">{content.formatJunit}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Theme */}
                  <div className="space-y-2">
                    <Label>{content.theme}</Label>
                    <Select
                      value={reportTheme}
                      onValueChange={(v) => setReportTheme(v as 'light' | 'dark' | 'professional')}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="professional">{content.themeProfessional}</SelectItem>
                        <SelectItem value="light">{content.themeLight}</SelectItem>
                        <SelectItem value="dark">{content.themeDark}</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Max Scores */}
                  <div className="space-y-2">
                    <Label>{content.maxScores}</Label>
                    <Input
                      type="number"
                      value={maxScores || ''}
                      onChange={(e) =>
                        setMaxScores(e.target.value ? Number(e.target.value) : undefined)
                      }
                      placeholder="All"
                      min={1}
                    />
                  </div>
                </div>

                {/* Options */}
                <div className="flex items-center space-x-2">
                  <Switch
                    id="include-charts"
                    checked={includeCharts}
                    onCheckedChange={setIncludeCharts}
                  />
                  <Label htmlFor="include-charts">{content.includeCharts}</Label>
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Button onClick={handlePreviewReport} variant="outline" disabled={generating}>
                    <Eye className="mr-2 h-4 w-4" />
                    {content.previewReport}
                  </Button>
                  <Button onClick={handleGenerateReport} disabled={generating}>
                    {generating ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Download className="mr-2 h-4 w-4" />
                    )}
                    {content.downloadReport}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      ) : (
        /* Empty State */
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold">{content.emptyTitle}</h3>
            <p className="text-muted-foreground text-center mt-2 max-w-md">
              {content.emptyDescription}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Preview Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{content.previewReport}</DialogTitle>
            <DialogDescription>{content.formatHtmlDesc}</DialogDescription>
          </DialogHeader>
          {reportPreview && (
            <div
              className="border rounded-lg p-4 bg-white"
              dangerouslySetInnerHTML={{ __html: reportPreview }}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
