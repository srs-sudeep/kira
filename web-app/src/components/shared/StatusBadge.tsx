import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import type { ReservationStatus } from '@/types/reservation'
import type { SyncStatus } from '@/types/channel'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
  {
    variants: {
      variant: {
        confirmed:   'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-950 dark:text-green-300',
        pending:     'bg-yellow-50 text-yellow-700 ring-yellow-600/20 dark:bg-yellow-950 dark:text-yellow-300',
        cancelled:   'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-950 dark:text-red-300',
        no_show:     'bg-orange-50 text-orange-700 ring-orange-600/20 dark:bg-orange-950 dark:text-orange-300',
        checked_in:  'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-950 dark:text-blue-300',
        checked_out: 'bg-slate-50 text-slate-700 ring-slate-600/20 dark:bg-slate-900 dark:text-slate-300',
        synced:      'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-950 dark:text-green-300',
        failed:      'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-950 dark:text-red-300',
        partial:     'bg-yellow-50 text-yellow-700 ring-yellow-600/20 dark:bg-yellow-950 dark:text-yellow-300',
        active:      'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-950 dark:text-green-300',
        inactive:    'bg-slate-50 text-slate-700 ring-slate-600/20 dark:bg-slate-900 dark:text-slate-300',
        default:     'bg-slate-50 text-slate-700 ring-slate-600/20 dark:bg-slate-900 dark:text-slate-300',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

type StatusVariant = VariantProps<typeof badgeVariants>['variant']

const LABELS: Record<string, string> = {
  confirmed:   'Confirmed',
  pending:     'Pending',
  cancelled:   'Cancelled',
  no_show:     'No Show',
  checked_in:  'Checked In',
  checked_out: 'Checked Out',
  synced:      'Synced',
  failed:      'Failed',
  partial:     'Partial',
  active:      'Active',
  inactive:    'Inactive',
}

interface StatusBadgeProps {
  status: ReservationStatus | SyncStatus | 'active' | 'inactive' | string
  label?: string
  className?: string
}

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const variant = (status as StatusVariant) ?? 'default'
  const displayLabel = label ?? LABELS[status] ?? status

  return (
    <span className={cn(badgeVariants({ variant }), className)}>
      {displayLabel}
    </span>
  )
}
