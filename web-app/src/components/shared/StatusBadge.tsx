import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import type { ReservationStatus } from '@/types/reservation'
import type { SyncStatus } from '@/types/channel'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold',
  {
    variants: {
      variant: {
        confirmed:   'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400',
        pending:     'bg-amber-500/10 text-amber-600 dark:bg-amber-500/15 dark:text-amber-400',
        cancelled:   'bg-red-500/10 text-red-600 dark:bg-red-500/15 dark:text-red-400',
        no_show:     'bg-orange-500/10 text-orange-600 dark:bg-orange-500/15 dark:text-orange-400',
        checked_in:  'bg-blue-500/10 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400',
        checked_out: 'bg-slate-500/10 text-slate-600 dark:bg-slate-500/15 dark:text-slate-400',
        synced:      'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400',
        failed:      'bg-red-500/10 text-red-600 dark:bg-red-500/15 dark:text-red-400',
        partial:     'bg-amber-500/10 text-amber-600 dark:bg-amber-500/15 dark:text-amber-400',
        active:      'bg-emerald-500/10 text-emerald-600 dark:bg-emerald-500/15 dark:text-emerald-400',
        inactive:    'bg-slate-500/10 text-slate-600 dark:bg-slate-500/15 dark:text-slate-400',
        default:     'bg-slate-500/10 text-slate-600 dark:bg-slate-500/15 dark:text-slate-400',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

type StatusVariant = VariantProps<typeof badgeVariants>['variant']

const LABELS: Record<string, string> = {
  confirmed: 'Confirmed', pending: 'Pending', cancelled: 'Cancelled',
  no_show: 'No Show', checked_in: 'Checked In', checked_out: 'Checked Out',
  synced: 'Synced', failed: 'Failed', partial: 'Partial',
  active: 'Active', inactive: 'Inactive',
}

interface StatusBadgeProps {
  status: ReservationStatus | SyncStatus | 'active' | 'inactive' | string
  label?: string
  className?: string
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const variant = (status as StatusVariant) ?? 'default'
  const displayLabel = label ?? LABELS[status] ?? status
  return <span className={cn(badgeVariants({ variant }), className)}>{displayLabel}</span>
}
