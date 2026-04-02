import { cn } from '@/lib/utils'
import type { SyncStatus } from '@/types/channel'

interface ChannelHealthBadgeProps {
  status: SyncStatus
  showLabel?: boolean
  className?: string
}

const CONFIG: Record<
  SyncStatus,
  { dot: string; bg: string; text: string; label: string; pulse: boolean }
> = {
  synced:  { dot: 'bg-accent-500',  bg: 'bg-accent-50 dark:bg-accent-950/50',  text: 'text-accent-700 dark:text-accent-400',  label: 'Synced',  pulse: false },
  pending: { dot: 'bg-yellow-400',  bg: 'bg-yellow-50 dark:bg-yellow-950/50',  text: 'text-yellow-700 dark:text-yellow-400',  label: 'Pending', pulse: true  },
  failed:  { dot: 'bg-red-500',     bg: 'bg-red-50 dark:bg-red-950/50',        text: 'text-destructive dark:text-red-400',    label: 'Failed',  pulse: false },
  partial: { dot: 'bg-orange-400',  bg: 'bg-orange-50 dark:bg-orange-950/50',  text: 'text-orange-700 dark:text-orange-400',  label: 'Partial', pulse: false },
}

export function ChannelHealthBadge({
  status,
  showLabel = true,
  className,
}: ChannelHealthBadgeProps) {
  const cfg = CONFIG[status] ?? CONFIG.pending

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ring-current/10',
        cfg.bg,
        cfg.text,
        className,
      )}
    >
      <span
        className={cn(
          'h-1.5 w-1.5 shrink-0 rounded-full',
          cfg.dot,
          cfg.pulse && 'animate-pulse',
        )}
      />
      {showLabel && cfg.label}
    </span>
  )
}
