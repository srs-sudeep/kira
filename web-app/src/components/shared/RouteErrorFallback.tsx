import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom'
import { AlertTriangle, Home, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/router/routes'
import { useAuthStore } from '@/stores/auth-store'
import { cn } from '@/lib/utils'

function messageFromUnknownData(data: unknown): string | null {
  if (data == null) return null
  if (typeof data === 'string') return data
  if (typeof data === 'object' && data !== null && 'detail' in data) {
    const d = (data as { detail: unknown }).detail
    if (typeof d === 'string') return d
    if (Array.isArray(d) && d[0] && typeof d[0] === 'object' && 'msg' in d[0]) {
      return String((d[0] as { msg?: string }).msg ?? '')
    }
  }
  return null
}

/**
 * React Router `errorElement` — handles loader/action throws, lazy chunk failures,
 * and route render errors that bubble to this boundary.
 */
export function RouteErrorFallback() {
  const error = useRouteError()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  let title = 'Something went wrong'
  let message =
    'We hit an unexpected problem. You can try again or go back to a safe page.'
  let status: number | undefined

  if (isRouteErrorResponse(error)) {
    status = error.status
    if (error.status === 404) {
      title = 'Page not found'
      message = "This page doesn't exist or was moved."
    } else {
      title = `Request error${error.status ? ` (${error.status})` : ''}`
    }
    const fromData = messageFromUnknownData(error.data)
    if (fromData) message = fromData
    else if (error.statusText) message = error.statusText
  } else if (error instanceof Error) {
    message = error.message
    if (
      error.message.includes('Failed to fetch dynamically imported module') ||
      error.message.includes('Importing a module script failed')
    ) {
      title = 'App updated'
      message =
        'A new version is available or the page failed to load. Reload to get the latest bundle.'
    }
  }

  const safeHref = isAuthenticated ? ROUTES.DASHBOARD : ROUTES.LOGIN
  const safeLabel = isAuthenticated ? 'Dashboard' : 'Sign in'

  return (
    <div
      className={cn(
        'flex min-h-screen flex-col items-center justify-center bg-background p-6',
      )}
    >
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 text-center shadow-sm">
        {status !== undefined && (
          <p className="mb-2 font-mono text-xs text-muted-foreground">{status}</p>
        )}
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-rose-500/10 to-red-500/10 dark:from-rose-500/20 dark:to-red-500/20">
          <AlertTriangle className="h-7 w-7 text-destructive/80" aria-hidden />
        </div>
        <h1 className="text-lg font-semibold tracking-tight text-foreground">{title}</h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{message}</p>
        <div className="mt-8 flex flex-col gap-2 sm:flex-row sm:justify-center">
          <Button variant="default" className="gap-2" asChild>
            <Link to={safeHref} replace>
              <Home className="h-4 w-4" />
              {safeLabel}
            </Link>
          </Button>
          <Button
            type="button"
            variant="outline"
            className="gap-2"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="h-4 w-4" />
            Reload page
          </Button>
        </div>
      </div>
    </div>
  )
}
