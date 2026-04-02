import { useState } from 'react'
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
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { format, parseISO } from 'date-fns'
import dashboardService from '../services/dashboard-service'

type DayRange = 7 | 30 | 90

const RANGES: { value: DayRange; label: string }[] = [
  { value: 7, label: '7d' },
  { value: 30, label: '30d' },
  { value: 90, label: '90d' },
]

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-md text-xs">
      <p className="mb-1 font-medium text-foreground">
        {label ? format(parseISO(label), 'dd MMM yyyy') : ''}
      </p>
      <p className="text-muted-foreground">
        Occupancy:{' '}
        <span className="font-semibold text-brand-600">
          {payload[0]?.value?.toFixed(1)}%
        </span>
      </p>
      {payload[1] && (
        <p className="text-muted-foreground">
          Rooms: {payload[1].payload.occupied_rooms} / {payload[1].payload.available_rooms + payload[1].payload.occupied_rooms}
        </p>
      )}
    </div>
  )
}

export function OccupancyChart() {
  const [range, setRange] = useState<DayRange>(30)

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

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-semibold">Occupancy Trend</CardTitle>
        <div className="flex items-center gap-1">
          {RANGES.map(({ value, label }) => (
            <Button
              key={value}
              variant={range === value ? 'default' : 'ghost'}
              size="sm"
              className={cn('h-7 px-2.5 text-xs', range !== value && 'text-muted-foreground')}
              onClick={() => setRange(value)}
            >
              {label}
            </Button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="h-48 animate-pulse rounded-lg bg-muted" />
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart
              data={data}
              margin={{ top: 4, right: 4, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="occupancyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563eb" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke="hsl(var(--border))"
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
                stroke="#2563eb"
                strokeWidth={2}
                fill="url(#occupancyGradient)"
                dot={false}
                activeDot={{ r: 4, fill: '#2563eb', strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
