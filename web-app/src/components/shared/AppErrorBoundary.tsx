import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Catches synchronous React render errors under the outlet that are not always
 * surfaced through React Router’s `errorElement`.
 */
export class AppErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('AppErrorBoundary', error, info.componentStack)
  }

  render() {
    if (this.state.hasError && this.state.error) {
      return (
        <div className="flex min-h-[50vh] flex-col items-center justify-center bg-background p-6">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500/10 to-red-500/10">
              <AlertTriangle className="h-7 w-7 text-destructive/80" aria-hidden />
            </div>
            <h1 className="text-lg font-semibold text-foreground">This view crashed</h1>
            <p className="mt-2 break-words text-sm text-muted-foreground">
              {this.state.error.message}
            </p>
            <Button
              type="button"
              variant="outline"
              className="mt-6 gap-2"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              <RefreshCw className="h-4 w-4" />
              Try again
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
