import { cn } from '@/lib/utils'

interface LoadingStateProps {
  message?: string
  fullScreen?: boolean
  className?: string
}

export function LoadingState({ message = 'Loading…', fullScreen, className }: LoadingStateProps) {
  return (
    <div
      className={cn(
        'flex items-center justify-center',
        fullScreen ? 'fixed inset-0 bg-background/80 backdrop-blur-sm z-50' : 'py-16',
        className,
      )}
    >
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-brand-600" />
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  )
}
