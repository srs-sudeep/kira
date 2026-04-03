/* global document, MutationObserver -- browser */
import { useState, useSyncExternalStore } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  type TooltipProps,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { format, parseISO } from 'date-fns'
import dashboardService from '../services/dashboard-service'

type DayRange = 7 | 30 | 90

const RANGES: { value: DayRange; label: string }[] = [
  { value: 7, label: '7d' },
  { value: 30, label: '30d' },
  { value: 90, label: '90d' },
]

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

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-xl border border-border/40 bg-card/95 glass px-3 py-2 shadow-xl text-xs">
      <p className="mb-1 font-medium text-foreground">
        {label ? format(parseISO(label), 'dd MMM yyyy') : ''}
      </p>
      <p className="text-muted-foreground">
        Occupancy:{' '}
        <span className="font-semibold text-primary">{payload[0]?.value?.toFixed(1)}%</span>
      </p>
      {payload[1] && (
        <p className="text-muted-foreground">
          Rooms: {payload[1].payload.occupied_rooms} /{' '}
          {payload[1].payload.available_rooms + payload[1].payload.occupied_rooms}
        </p>
      )}
    </div>
  )
}

export function OccupancyChart() {
  const [range, setRange] = useState<DayRange>(30)
  const isDark = useDarkMode()

  const { data = [], isLoading } = useQuery({
    queryKey: ['dashboard', 'occupancy-trend', range],
    queryFn: () => dashboardService.getOccupancyTrend(range),
  })

  const tickFormat = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), range === 7 ? 'EEE' : 'dd MMM')
    } catch {
      return dateStr
    }
  }

  const gradientId = isDark ? 'occupancyGradientDark' : 'occupancyGradient'

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-semibold">Occupancy Trend</CardTitle>
        <div className="flex items-center gap-1 rounded-full bg-muted/50 p-0.5">
          {RANGES.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              className={cn(
                'rounded-full px-2.5 py-1 text-xs font-medium transition-all',
                range === value
                  ? 'bg-background text-foreground shadow-sm dark:bg-primary/20 dark:text-primary dark:shadow-[0_0_14px_hsl(var(--primary)/0.35)]'
                  : 'text-muted-foreground hover:text-foreground',
              )}
              onClick={() => setRange(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[200px] w-full rounded-lg" />
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="occupancyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.18} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="occupancyGradientDark" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.6} />
                  <stop offset="50%" stopColor="hsl(var(--primary))" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="hsl(var(--border) / 0.4)"
                vertical={false}
              />
              <XAxis
                dataKey="date"
                tickFormatter={tickFormat}
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, 100]}
                tickFormatter={(v: number) => `${v}%`}
                tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                axisLine={false}
                tickLine={false}
                width={40}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="occupancy_pct"
                stroke="hsl(var(--primary))"
                strokeWidth={isDark ? 2.5 : 2}
                fill={`url(#${gradientId})`}
                dot={false}
                activeDot={{
                  r: 5,
                  fill: 'hsl(var(--primary))',
                  stroke: isDark ? 'hsl(var(--primary))' : 'hsl(var(--background))',
                  strokeWidth: isDark ? 4 : 2,
                  strokeOpacity: isDark ? 0.3 : 1,
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
