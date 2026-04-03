import { cn } from '@/lib/utils'
import type { SyncStatus } from '@/types/channel'

interface ChannelHealthBadgeProps {
  status: SyncStatus
  showLabel?: boolean
  className?: string
}

const CONFIG: Record<
  SyncStatus,
  { dot: string; glow: string; bg: string; text: string; label: string; pulse: boolean }
> = {
  synced: {
    dot: 'bg-emerald-400',
    glow: 'shadow-[0_0_10px_rgba(52,211,153,0.55)] dark:shadow-[0_0_12px_rgba(52,211,153,0.45)]',
    bg: 'bg-emerald-500/[0.08] dark:bg-emerald-500/[0.12]',
    text: 'text-emerald-600 dark:text-emerald-400',
    label: 'Synced',
    pulse: false,
  },
  pending: {
    dot: 'bg-amber-400',
    glow: 'shadow-[0_0_10px_rgba(251,191,36,0.55)] dark:shadow-[0_0_12px_rgba(251,191,36,0.45)]',
    bg: 'bg-amber-500/[0.08] dark:bg-amber-500/[0.12]',
    text: 'text-amber-600 dark:text-amber-400',
    label: 'Pending',
    pulse: true,
  },
  failed: {
    dot: 'bg-red-400',
    glow: 'shadow-[0_0_10px_rgba(248,113,113,0.55)] dark:shadow-[0_0_12px_rgba(248,113,113,0.45)]',
    bg: 'bg-red-500/[0.08] dark:bg-red-500/[0.12]',
    text: 'text-red-600 dark:text-red-400',
    label: 'Failed',
    pulse: false,
  },
  partial: {
    dot: 'bg-orange-400',
    glow: 'shadow-[0_0_10px_rgba(251,146,60,0.5)] dark:shadow-[0_0_12px_rgba(251,146,60,0.42)]',
    bg: 'bg-orange-500/[0.08] dark:bg-orange-500/[0.12]',
    text: 'text-orange-600 dark:text-orange-400',
    label: 'Partial',
    pulse: false,
  },
}

export function ChannelHealthBadge({ status, showLabel = true, className }: ChannelHealthBadgeProps) {
  const cfg = CONFIG[status] ?? CONFIG.pending
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold',
        cfg.bg,
        cfg.text,
        className,
      )}
    >
      <span
        className={cn(
          'h-1.5 w-1.5 shrink-0 rounded-full',
          cfg.dot,
          cfg.glow,
          cfg.pulse && 'animate-pulse',
        )}
      />
      {showLabel && cfg.label}
    </span>
  )
}
