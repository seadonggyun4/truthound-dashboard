import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-[80vh] flex-col items-center justify-center gap-4 p-6">
          <AlertTriangle className="h-12 w-12 text-orange-500" />
          <h2 className="text-xl font-semibold">Something went wrong</h2>
          <p className="max-w-md text-center text-sm text-muted-foreground">
            An unexpected error occurred. This may be caused by a temporary issue.
          </p>
          <div className="flex gap-2">
            <button
              onClick={this.handleReset}
              className="inline-flex items-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              Try Again
            </button>
            <button
              onClick={this.handleReload}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              <RefreshCw className="h-4 w-4" />
              Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
