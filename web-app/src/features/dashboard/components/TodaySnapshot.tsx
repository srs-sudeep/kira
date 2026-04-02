import { useQuery } from '@tanstack/react-query'
import { ArrowDownToLine, ArrowUpFromLine, BedDouble, UserX } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import dashboardService from '../services/dashboard-service'

interface SnapshotRowProps {
  icon: React.ElementType
  label: string
  value: number
  iconClassName?: string
}

function SnapshotRow({ icon: Icon, label, value, iconClassName }: SnapshotRowProps) {
  return (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center gap-3">
        <div className={`flex h-7 w-7 items-center justify-center rounded-md ${iconClassName}`}>
          <Icon className="h-4 w-4" />
        </div>
        <span className="text-sm text-muted-foreground">{label}</span>
      </div>
      <span className="text-sm font-semibold tabular-nums text-foreground">{value}</span>
    </div>
  )
}

export function TodaySnapshot() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard', 'today-snapshot'],
    queryFn: dashboardService.getTodaySnapshot,
  })

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">Today</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="h-4 w-28 animate-pulse rounded bg-muted" />
                <div className="h-4 w-8 animate-pulse rounded bg-muted" />
              </div>
            ))}
          </div>
        ) : (
          <>
            <div className="divide-y divide-border">
              <SnapshotRow
                icon={ArrowDownToLine}
                label="Arrivals"
                value={data?.arrivals ?? 0}
                iconClassName="bg-blue-50 text-blue-600 dark:bg-blue-950 dark:text-blue-400"
              />
              <SnapshotRow
                icon={ArrowUpFromLine}
                label="Departures"
                value={data?.departures ?? 0}
                iconClassName="bg-orange-50 text-orange-600 dark:bg-orange-950 dark:text-orange-400"
              />
              <SnapshotRow
                icon={BedDouble}
                label="Stay-overs"
                value={data?.stay_overs ?? 0}
                iconClassName="bg-accent-50 text-accent-600 dark:bg-accent-950 dark:text-accent-400"
              />
              <SnapshotRow
                icon={UserX}
                label="No-shows"
                value={data?.no_shows ?? 0}
                iconClassName="bg-red-50 text-red-600 dark:bg-red-950 dark:text-red-400"
              />
            </div>

            {/* Occupancy bar */}
            <div className="mt-4">
              <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                <span>Occupancy</span>
                <span className="font-semibold text-foreground">
                  {data?.occupied_rooms ?? 0} / {data?.total_rooms ?? 0} rooms
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-brand-500 transition-all duration-500"
                  style={{ width: `${data?.occupancy_pct ?? 0}%` }}
                />
              </div>
              <p className="mt-1 text-right text-xs font-medium text-brand-600">
                {(data?.occupancy_pct ?? 0).toFixed(1)}%
              </p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
