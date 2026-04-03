import { cn } from '@/lib/utils'

interface LoadingStateProps {
  message?: string
  fullScreen?: boolean
  className?: string
}

function SkeletonPulse({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'rounded-lg bg-gradient-to-r from-muted via-muted/60 to-muted bg-[length:200%_100%] animate-[shimmer_1.5s_ease-in-out_infinite]',
        className,
      )}
    />
  )
}

export function LoadingState({ message, fullScreen, className }: LoadingStateProps) {
  if (fullScreen) {
    return (
      <div className={cn('fixed inset-0 z-50 flex items-center justify-center bg-background/80 glass', className)}>
        <div className="flex flex-col items-center gap-4">
          <div className="relative h-10 w-10">
            <div className="absolute inset-0 rounded-full border-[3px] border-muted" />
            <div className="absolute inset-0 animate-spin rounded-full border-[3px] border-transparent border-t-brand-500" />
          </div>
          {message && <p className="text-sm font-medium text-muted-foreground">{message}</p>}
        </div>
      </div>
    )
  }

  return (
    <div className={cn('space-y-6 py-4', className)}>
      {/* KPI row skeleton */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border border-border/60 bg-card p-5">
            <div className="space-y-3">
              <SkeletonPulse className="h-3.5 w-24" />
              <SkeletonPulse className="h-7 w-32" />
              <SkeletonPulse className="h-3 w-20" />
            </div>
          </div>
        ))}
      </div>

      {/* Chart skeleton */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border border-border/60 bg-card p-5">
          <SkeletonPulse className="h-4 w-36 mb-4" />
          <SkeletonPulse className="h-48 w-full rounded-lg" />
        </div>
        <div className="rounded-xl border border-border/60 bg-card p-5">
          <SkeletonPulse className="h-4 w-28 mb-4" />
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <SkeletonPulse className="h-3.5 w-24" />
                <SkeletonPulse className="h-5 w-12 rounded-full" />
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Table skeleton */}
      <div className="rounded-xl border border-border/60 bg-card p-5">
        <SkeletonPulse className="h-4 w-40 mb-4" />
        <div className="space-y-2.5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <SkeletonPulse className="h-8 w-8 rounded-full" />
              <SkeletonPulse className="h-3.5 flex-1" />
              <SkeletonPulse className="h-3.5 w-20" />
              <SkeletonPulse className="h-5 w-16 rounded-full" />
            </div>
          ))}
        </div>
      </div>

      {message && (
        <p className="text-center text-sm text-muted-foreground">{message}</p>
      )}
    </div>
  )
}

export { SkeletonPulse }
