import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Database,
  Play,
  FileCode,
  History,
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Settings2,
  BarChart3,
  Sliders,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  getSource,
  getSourceSchema,
  listSourceValidations,
  runValidation,
  learnSchema,
  listValidators,
  type Source,
  type Schema,
  type Validation,
  type ValidatorDefinition,
  type ValidatorConfig,
} from '@/api/client'
import { formatDate, formatDuration, formatNumber } from '@/lib/utils'
import { useToast } from '@/hooks/use-toast'
import { ValidatorSelector } from '@/components/validators'

export default function SourceDetail() {
  const { id } = useParams<{ id: string }>()
  const [source, setSource] = useState<Source | null>(null)
  const [schema, setSchema] = useState<Schema | null>(null)
  const [validations, setValidations] = useState<Validation[]>([])
  const [loading, setLoading] = useState(true)
  const [validating, setValidating] = useState(false)
  const [validationDialogOpen, setValidationDialogOpen] = useState(false)
  const [validators, setValidators] = useState<ValidatorDefinition[]>([])
  const [validatorConfigs, setValidatorConfigs] = useState<ValidatorConfig[]>([])
  const [loadingValidators, setLoadingValidators] = useState(false)
  const { toast } = useToast()

  const loadData = useCallback(async () => {
    if (!id) return
    try {
      setLoading(true)
      const [sourceData, schemaData, validationsData] = await Promise.all([
        getSource(id),
        getSourceSchema(id),
        listSourceValidations(id),
      ])
      setSource(sourceData)
      setSchema(schemaData)
      setValidations(validationsData.data)
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load source details',
        variant: 'destructive',
      })
    } finally {
      setLoading(false)
    }
  }, [id, toast])

  const loadValidators = useCallback(async () => {
    if (validators.length > 0) return // Already loaded
    try {
      setLoadingValidators(true)
      const validatorDefs = await listValidators()
      setValidators(validatorDefs)
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to load validators',
        variant: 'destructive',
      })
    } finally {
      setLoadingValidators(false)
    }
  }, [validators.length, toast])

  useEffect(() => {
    loadData()
  }, [loadData])

  async function handleValidate() {
    if (!id) return
    try {
      setValidating(true)
      // Get enabled validators with their configurations
      const enabledConfigs = validatorConfigs.filter((c) => c.enabled)
      const options = enabledConfigs.length > 0 ? { validator_configs: enabledConfigs } : {}
      const result = await runValidation(id, options)
      setValidations((prev) => [result, ...prev])
      setValidationDialogOpen(false)
      toast({
        title: result.passed ? 'Validation Passed' : 'Validation Failed',
        description: `Found ${result.total_issues} issues`,
        variant: result.passed ? 'default' : 'destructive',
      })
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to run validation',
        variant: 'destructive',
      })
    } finally {
      setValidating(false)
    }
  }

  async function handleQuickValidate() {
    if (!id) return
    try {
      setValidating(true)
      const result = await runValidation(id, {})
      setValidations((prev) => [result, ...prev])
      toast({
        title: result.passed ? 'Validation Passed' : 'Validation Failed',
        description: `Found ${result.total_issues} issues`,
        variant: result.passed ? 'default' : 'destructive',
      })
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to run validation',
        variant: 'destructive',
      })
    } finally {
      setValidating(false)
    }
  }

  function handleOpenValidationDialog() {
    loadValidators()
    setValidationDialogOpen(true)
  }

  async function handleLearnSchema() {
    if (!id) return
    try {
      toast({
        title: 'Learning Schema',
        description: 'Analyzing data structure...',
      })
      const result = await learnSchema(id)
      setSchema(result)
      toast({
        title: 'Schema Learned',
        description: `Found ${result.column_count} columns`,
      })
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to learn schema',
        variant: 'destructive',
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  if (!source) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <XCircle className="h-12 w-12 text-destructive mb-4" />
        <p className="text-muted-foreground">Source not found</p>
        <Button asChild className="mt-4">
          <Link to="/sources">Back to Sources</Link>
        </Button>
      </div>
    )
  }

  const latestValidation = validations[0]

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link
        to="/sources"
        className="inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Sources
      </Link>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="h-14 w-14 rounded-lg bg-primary/10 flex items-center justify-center">
            <Database className="h-7 w-7 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">{source.name}</h1>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="outline">{source.type}</Badge>
              {source.is_active ? (
                <Badge variant="success">Active</Badge>
              ) : (
                <Badge variant="secondary">Inactive</Badge>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" asChild>
            <Link to={`/sources/${id}/rules`}>
              <Settings2 className="mr-2 h-4 w-4" />
              Rules
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/sources/${id}/profile`}>
              <BarChart3 className="mr-2 h-4 w-4" />
              Profile
            </Link>
          </Button>
          <Button variant="outline" asChild>
            <Link to={`/sources/${id}/history`}>
              <History className="mr-2 h-4 w-4" />
              History
            </Link>
          </Button>
          <Button variant="outline" onClick={handleLearnSchema}>
            <FileCode className="mr-2 h-4 w-4" />
            Learn Schema
          </Button>
          <Button variant="outline" onClick={handleQuickValidate} disabled={validating}>
            <Play className="mr-2 h-4 w-4" />
            {validating ? 'Validating...' : 'Quick Validate'}
          </Button>
          <Dialog open={validationDialogOpen} onOpenChange={setValidationDialogOpen}>
            <DialogTrigger asChild>
              <Button onClick={handleOpenValidationDialog} disabled={validating}>
                <Sliders className="mr-2 h-4 w-4" />
                Configure & Run
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Configure Validation</DialogTitle>
                <DialogDescription>
                  Select and configure validators to run against this data source.
                  Use presets for quick setup or customize individual validators.
                </DialogDescription>
              </DialogHeader>
              <div className="py-4">
                {loadingValidators ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
                  </div>
                ) : (
                  <ValidatorSelector
                    validators={validators}
                    configs={validatorConfigs}
                    onChange={setValidatorConfigs}
                    columns={schema?.columns || []}
                  />
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setValidationDialogOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleValidate} disabled={validating}>
                  <Play className="mr-2 h-4 w-4" />
                  {validating ? 'Validating...' : 'Run Validation'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Status</p>
                <div className="flex items-center gap-2 mt-1">
                  {latestValidation?.passed ? (
                    <>
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      <span className="font-semibold text-green-600">Passed</span>
                    </>
                  ) : latestValidation ? (
                    <>
                      <XCircle className="h-5 w-5 text-red-600" />
                      <span className="font-semibold text-red-600">Failed</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="h-5 w-5 text-yellow-600" />
                      <span className="font-semibold text-yellow-600">
                        Not Validated
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Total Issues</p>
            <p className="text-2xl font-bold mt-1">
              {formatNumber(latestValidation?.total_issues)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Rows</p>
            <p className="text-2xl font-bold mt-1">
              {formatNumber(latestValidation?.row_count)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Last Validation</p>
            <p className="text-lg font-medium mt-1">
              {formatDate(source.last_validated_at)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Latest Issues */}
      {latestValidation && latestValidation.issues.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-600" />
              Issues Found ({latestValidation.total_issues})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {latestValidation.issues.slice(0, 10).map((issue, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="flex items-center gap-3">
                    <Badge
                      variant={
                        issue.severity === 'critical'
                          ? 'critical'
                          : issue.severity === 'high'
                          ? 'high'
                          : issue.severity === 'medium'
                          ? 'medium'
                          : 'low'
                      }
                    >
                      {issue.severity}
                    </Badge>
                    <div>
                      <p className="font-medium">
                        {issue.column}: {issue.issue_type}
                      </p>
                      {issue.details && (
                        <p className="text-sm text-muted-foreground">
                          {issue.details}
                        </p>
                      )}
                    </div>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {formatNumber(issue.count)} occurrences
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Schema */}
      {schema && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileCode className="h-5 w-5" />
              Schema ({schema.column_count} columns)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {schema.columns.map((col) => (
                <Badge key={col} variant="outline">
                  {col}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Validation History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Validation History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {validations.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No validations yet. Run your first validation to see results here.
            </p>
          ) : (
            <div className="space-y-3">
              {validations.map((validation) => (
                <Link
                  key={validation.id}
                  to={`/validations/${validation.id}`}
                  className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {validation.passed ? (
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-600" />
                    )}
                    <div>
                      <p className="font-medium">
                        {validation.passed ? 'Passed' : 'Failed'} -{' '}
                        {formatNumber(validation.total_issues)} issues
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {formatDate(validation.created_at)} •{' '}
                        {formatDuration(validation.duration_ms)}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {validation.critical_issues > 0 && (
                      <Badge variant="critical">
                        {validation.critical_issues} critical
                      </Badge>
                    )}
                    {validation.high_issues > 0 && (
                      <Badge variant="high">{validation.high_issues} high</Badge>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
