import { useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO, isToday, isWeekend } from 'date-fns'
import { toast } from 'sonner'
import { AriCell } from './AriCell'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import type { CalendarRow } from '../services/inventory-service'
import inventoryService, { type DayUpdatePayload } from '../services/inventory-service'

interface AriCalendarGridProps {
  rows: CalendarRow[]
  dates: string[]
  queryKey: readonly unknown[]
  isLoading?: boolean
}

function CalendarSkeleton({ dates }: { dates: string[] }) {
  const colCount = Math.max(dates.length, 7)
  return (
    <div className="overflow-auto rounded-xl border border-border/30 bg-card/60 glass shadow-lg">
      <table className="border-collapse">
        <thead>
          <tr className="sticky top-0 z-20 border-b border-border/30 bg-card/80 backdrop-blur-md">
            <th className="sticky left-0 z-30 min-w-[200px] border-r border-border/30 bg-card/80 px-3 py-2">
              <Skeleton className="h-3 w-28" />
            </th>
            {Array.from({ length: colCount }).map((_, i) => (
              <th key={i} className="min-w-[80px] border-r border-border/30 px-1 py-2">
                <Skeleton className="mx-auto h-8 w-12 rounded-md" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 6 }).map((_, rowIdx) => (
            <tr
              key={rowIdx}
              className={cn(
                'border-b border-border/25',
                rowIdx % 2 === 1 && 'bg-muted/[0.04]',
              )}
            >
              <td className="sticky left-0 z-10 min-w-[200px] border-r border-border/30 bg-card/70 px-3 py-2 backdrop-blur-sm">
                <Skeleton className="h-3.5 w-32" />
                <Skeleton className="mt-1.5 h-2.5 w-24" />
              </td>
              {Array.from({ length: colCount }).map((__, ci) => (
                <td key={ci} className="border-r border-border/30 p-1.5">
                  <Skeleton className="h-14 w-full rounded-md" />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-4 border-t border-border/30 bg-card/50 px-4 py-2 backdrop-blur-sm">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-40" />
      </div>
    </div>
  )
}

export function AriCalendarGrid({ rows, dates, queryKey, isLoading }: AriCalendarGridProps) {
  const qc = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: (vars: {
      roomTypeId: string
      ratePlanId: string
      date: string
      updates: DayUpdatePayload
    }) => inventoryService.updateDay(vars.roomTypeId, vars.ratePlanId, vars.date, vars.updates),
    onMutate: async (vars) => {
      await qc.cancelQueries({ queryKey })
      const snapshot = qc.getQueryData<CalendarRow[]>(queryKey)
      qc.setQueryData<CalendarRow[]>(queryKey, (old) => {
        if (!old) return old
        return old.map((row) => {
          if (row.room_type_id !== vars.roomTypeId || row.rate_plan_id !== vars.ratePlanId) return row
          return {
            ...row,
            days: row.days.map((day) => (day.date === vars.date ? { ...day, ...vars.updates } : day)),
          }
        })
      })
      return { snapshot }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.snapshot) qc.setQueryData(queryKey, ctx.snapshot)
      toast.error('Failed to update — changes reverted')
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey })
    },
  })

  async function handleCellSave(
    roomTypeId: string,
    ratePlanId: string,
    date: string,
    updates: DayUpdatePayload,
  ) {
    await updateMutation.mutateAsync({ roomTypeId, ratePlanId, date, updates })
  }

  if (isLoading) {
    return <CalendarSkeleton dates={dates} />
  }

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-border/30 bg-card/60 glass p-16 text-center text-sm text-muted-foreground shadow-lg backdrop-blur-md">
        No inventory data for this selection.
      </div>
    )
  }

  return (
    <div className="overflow-auto rounded-xl border border-border/30 bg-card/60 glass shadow-lg backdrop-blur-md">
      <table className="border-collapse">
        <thead>
          <tr className="sticky top-0 z-20 border-b border-border/30 bg-card/85 backdrop-blur-md">
            <th className="sticky left-0 z-30 min-w-[200px] border-r border-border/30 bg-card/90 px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground/65 backdrop-blur-md">
              Room · Rate Plan
            </th>
            {dates.map((date) => {
              const d = parseISO(date)
              const today = isToday(d)
              const weekend = isWeekend(d)
              return (
                <th
                  key={date}
                  className={cn(
                    'min-w-[80px] border-r border-border/30 px-1 py-1 text-center text-[10px] transition-colors',
                    today &&
                      'bg-primary/[0.06] shadow-[inset_0_0_28px_hsl(var(--primary)/0.14)] dark:bg-primary/[0.1] dark:shadow-[inset_0_0_32px_hsl(var(--primary)/0.18)]',
                    weekend && !today && 'bg-muted/[0.18]',
                  )}
                >
                  <div className={cn('font-medium', today ? 'text-primary' : 'text-muted-foreground')}>
                    {format(d, 'EEE')}
                  </div>
                  <div className={cn('font-semibold', today ? 'text-primary' : 'text-foreground')}>
                    {format(d, 'dd')}
                  </div>
                  <div className="text-[9px] text-muted-foreground/55">{format(d, 'MMM')}</div>
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIdx) => (
            <tr
              key={`${row.room_type_id}-${row.rate_plan_id}`}
              className={cn(
                'border-b border-border/25 transition-colors hover:bg-muted/[0.08]',
                rowIdx % 2 === 1 && 'bg-muted/[0.035]',
              )}
            >
              <td className="sticky left-0 z-10 min-w-[200px] border-r border-border/30 bg-card/80 px-3 py-2 backdrop-blur-sm">
                <p className="text-xs font-semibold text-foreground">{row.room_type_name}</p>
                <p className="text-[10px] text-muted-foreground/65">{row.rate_plan_name}</p>
              </td>
              {dates.map((date) => {
                const day = row.days.find((d) => d.date === date)
                const today = isToday(parseISO(date))
                return (
                  <td
                    key={date}
                    className={cn(
                      'border-r border-border/30 p-0',
                      today &&
                        'bg-primary/[0.04] shadow-[inset_0_0_22px_hsl(var(--primary)/0.1)] dark:bg-primary/[0.06] dark:shadow-[inset_0_0_24px_hsl(var(--primary)/0.12)]',
                    )}
                  >
                    <AriCell
                      day={day}
                      onSave={(updates) => handleCellSave(row.room_type_id, row.rate_plan_id, date, updates)}
                    />
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex items-center gap-4 border-t border-border/30 bg-card/55 px-4 py-2 text-[10px] text-muted-foreground/65 backdrop-blur-sm">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm bg-emerald-500/12 dark:bg-emerald-500/18" />
          Available
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm bg-amber-500/12 dark:bg-amber-500/18" />
          Low (≤2)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm bg-red-500/12 dark:bg-red-500/18" />
          Sold / Stop Sell / Closed
        </span>
        <span className="ml-auto">
          Click a cell to edit rate & availability · Enter to save · Esc to cancel
        </span>
      </div>
    </div>
  )
}
