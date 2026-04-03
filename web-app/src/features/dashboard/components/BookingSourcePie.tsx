/* global document, MutationObserver -- browser */
import { useSyncExternalStore } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
  type TooltipProps,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CurrencyDisplay } from '@/components/shared/CurrencyDisplay'
import { Skeleton } from '@/components/ui/skeleton'
import dashboardService from '../services/dashboard-service'

/** Light mode — saturated, readable on white */
const PALETTE_LIGHT = ['#6366f1', '#0ea5e9', '#10b981', '#f59e0b', '#8b5cf6']
/** Dark mode — neon / high chroma */
const PALETTE_DARK = ['#a5b4fc', '#22d3ee', '#34d399', '#fbbf24', '#c4b5fd']

function useDarkMode() {
  return useSyncExternalStore(
    (onStoreChange) => {
      const el = document.documentElement
      const obs = new MutationObserver(() => onStoreChange())
      obs.observe(el, { attributes: true, attributeFilter: ['class'] })
      return () => obs.disconnect()
    },
    () => document.documentElement.classList.contains('dark'),
    () => false,
  )
}

function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div className="rounded-xl border border-border/40 bg-card/95 glass px-3 py-2 shadow-xl text-xs">
      <p className="mb-1 font-medium text-foreground">{d.name}</p>
      <p className="text-muted-foreground">
        Bookings: <span className="font-semibold text-foreground">{d.value}</span>
      </p>
      <p className="text-muted-foreground">
        Share:{' '}
        <span className="font-semibold text-foreground">
          {d.payload?.percentage?.toFixed(1)}%
        </span>
      </p>
    </div>
  )
}

function CustomLegend({
  payload,
}: {
  payload?: Array<{ value: string; color: string; payload: { revenue?: number } }>
}) {
  return (
    <ul className="mt-2 space-y-1.5">
      {(payload ?? []).map((entry) => (
        <li key={entry.value} className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <span
              className="inline-block h-2 w-2 shrink-0 rounded-full opacity-90"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground/80">{entry.value}</span>
          </div>
          {entry.payload?.revenue !== undefined && (
            <CurrencyDisplay amount={entry.payload.revenue} size="sm" className="text-xs text-muted-foreground/90" />
          )}
        </li>
      ))}
    </ul>
  )
}

export function BookingSourcePie() {
  const isDark = useDarkMode()
  const palette = isDark ? PALETTE_DARK : PALETTE_LIGHT

  const { data = [], isLoading } = useQuery({
    queryKey: ['dashboard', 'booking-sources'],
    queryFn: () => dashboardService.getBookingSources(30),
  })

  const chartData = data.map((d) => ({
    name: d.display_name,
    value: d.count,
    percentage: d.percentage,
    revenue: d.revenue,
  }))

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-base font-semibold">Booking Sources</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex flex-col items-center gap-4">
            <Skeleton className="h-40 w-40 rounded-full" />
            <div className="w-full space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex justify-between">
                  <Skeleton className="h-3 w-28" />
                  <Skeleton className="h-3 w-16" />
                </div>
              ))}
            </div>
          </div>
        ) : chartData.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">No booking data available.</p>
        ) : (
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={70}
                paddingAngle={2}
                dataKey="value"
              >
                {chartData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={palette[index % palette.length]}
                    stroke="transparent"
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                content={
                  <CustomLegend
                    payload={chartData.map((d, i) => ({
                      value: d.name,
                      color: palette[i % palette.length],
                      payload: { revenue: d.revenue },
                    }))}
                  />
                }
              />
            </PieChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
