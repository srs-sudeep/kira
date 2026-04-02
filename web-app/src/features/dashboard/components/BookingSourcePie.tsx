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
import dashboardService from '../services/dashboard-service'

const PALETTE = [
  '#2563eb', // brand-600 — Booking.com
  '#0ea5e9', // sky-500 — Expedia
  '#22c55e', // accent-500 — MakeMyTrip
  '#f59e0b', // amber-400 — others
  '#8b5cf6', // violet-500
]

function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  const d = payload[0]
  return (
    <div className="rounded-lg border bg-card px-3 py-2 shadow-md text-xs">
      <p className="mb-1 font-medium text-foreground">{d.name}</p>
      <p className="text-muted-foreground">
        Bookings:{' '}
        <span className="font-semibold text-foreground">{d.value}</span>
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
              className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground">{entry.value}</span>
          </div>
          {entry.payload?.revenue !== undefined && (
            <CurrencyDisplay amount={entry.payload.revenue} size="sm" className="text-xs" />
          )}
        </li>
      ))}
    </ul>
  )
}

export function BookingSourcePie() {
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
            <div className="h-40 w-40 animate-pulse rounded-full bg-muted" />
            <div className="w-full space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex justify-between">
                  <div className="h-3 w-28 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-16 animate-pulse rounded bg-muted" />
                </div>
              ))}
            </div>
          </div>
        ) : chartData.length === 0 ? (
          <p className="py-8 text-center text-sm text-muted-foreground">
            No booking data available.
          </p>
        ) : (
          <>
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
                      fill={PALETTE[index % PALETTE.length]}
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
                        color: PALETTE[i % PALETTE.length],
                        payload: { revenue: d.revenue },
                      }))}
                    />
                  }
                />
              </PieChart>
            </ResponsiveContainer>
          </>
        )}
      </CardContent>
    </Card>
  )
}
