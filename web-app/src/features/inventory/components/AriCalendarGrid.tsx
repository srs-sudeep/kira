import { useMutation, useQueryClient } from '@tanstack/react-query'
import { format, parseISO, isToday, isWeekend } from 'date-fns'
import { toast } from 'sonner'
import { AriCell } from './AriCell'
import { cn } from '@/lib/utils'
import type { CalendarRow } from '../services/inventory-service'
import inventoryService, { type DayUpdatePayload } from '../services/inventory-service'

interface AriCalendarGridProps {
  rows: CalendarRow[]
  dates: string[]
  queryKey: readonly unknown[]
}

export function AriCalendarGrid({ rows, dates, queryKey }: AriCalendarGridProps) {
  const qc = useQueryClient()

  const updateMutation = useMutation({
    mutationFn: (vars: {
      roomTypeId: string
      ratePlanId: string
      date: string
      updates: DayUpdatePayload
    }) =>
      inventoryService.updateDay(
        vars.roomTypeId,
        vars.ratePlanId,
        vars.date,
        vars.updates,
      ),

    onMutate: async (vars) => {
      await qc.cancelQueries({ queryKey })
      const snapshot = qc.getQueryData<CalendarRow[]>(queryKey)

      qc.setQueryData<CalendarRow[]>(queryKey, (old) => {
        if (!old) return old
        return old.map((row) => {
          if (
            row.room_type_id !== vars.roomTypeId ||
            row.rate_plan_id !== vars.ratePlanId
          )
            return row
          return {
            ...row,
            days: row.days.map((day) =>
              day.date === vars.date ? { ...day, ...vars.updates } : day,
            ),
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

  if (rows.length === 0) {
    return (
      <div className="rounded-lg border bg-card p-16 text-center text-sm text-muted-foreground">
        No inventory data for this selection.
      </div>
    )
  }

  return (
    <div className="overflow-auto rounded-lg border">
      <table className="border-collapse">
        <thead>
          <tr className="sticky top-0 z-20 border-b bg-card">
            {/* Room / Rate label column */}
            <th className="sticky left-0 z-30 min-w-[200px] border-r bg-card px-3 py-2 text-left text-xs font-medium text-muted-foreground">
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
                    'min-w-[80px] border-r px-1 py-1 text-center text-[10px]',
                    today && 'bg-brand-50 dark:bg-brand-950/30',
                    weekend && !today && 'bg-muted/50',
                  )}
                >
                  <div
                    className={cn(
                      'font-medium',
                      today ? 'text-brand-600 dark:text-brand-400' : 'text-muted-foreground',
                    )}
                  >
                    {format(d, 'EEE')}
                  </div>
                  <div
                    className={cn(
                      'font-semibold',
                      today ? 'text-brand-600 dark:text-brand-400' : 'text-foreground',
                    )}
                  >
                    {format(d, 'dd')}
                  </div>
                  <div className="text-[9px] text-muted-foreground">
                    {format(d, 'MMM')}
                  </div>
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
                'border-b transition-colors hover:bg-muted/20',
                rowIdx % 2 === 1 && 'bg-muted/10',
              )}
            >
              {/* Sticky label */}
              <td className="sticky left-0 z-10 min-w-[200px] border-r bg-card px-3 py-2">
                <p className="text-xs font-semibold text-foreground">
                  {row.room_type_name}
                </p>
                <p className="text-[10px] text-muted-foreground">{row.rate_plan_name}</p>
              </td>

              {dates.map((date) => {
                const day = row.days.find((d) => d.date === date)
                const today = isToday(parseISO(date))
                return (
                  <td
                    key={date}
                    className={cn(
                      'border-r p-0',
                      today && 'ring-x ring-inset ring-brand-200 dark:ring-brand-800',
                    )}
                  >
                    <AriCell
                      day={day}
                      onSave={(updates) =>
                        handleCellSave(
                          row.room_type_id,
                          row.rate_plan_id,
                          date,
                          updates,
                        )
                      }
                    />
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Legend */}
      <div className="flex items-center gap-4 border-t bg-card px-4 py-2 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm bg-green-100 dark:bg-green-950" />
          Available
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm bg-yellow-100 dark:bg-yellow-950" />
          Low (≤2)
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-3 w-3 rounded-sm bg-red-100 dark:bg-red-950" />
          Sold / Stop Sell / Closed
        </span>
        <span className="ml-auto">Click a cell to edit rate &amp; availability · Enter to save · Esc to cancel</span>
      </div>
    </div>
  )
}
