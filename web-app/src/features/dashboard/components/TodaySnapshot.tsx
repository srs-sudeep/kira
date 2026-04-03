import type { ElementType } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ArrowDownToLine, ArrowUpFromLine, BedDouble, UserX } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import dashboardService from '../services/dashboard-service'

interface SnapshotRowProps {
  icon: ElementType
  label: string
  value: number
  iconClassName?: string
}

function SnapshotRow({ icon: Icon, label, value, iconClassName }: SnapshotRowProps) {
  return (
    <div className="flex items-center justify-between py-2.5">
      <div className="flex items-center gap-3">
        <div className={`flex h-8 w-8 items-center justify-center rounded-xl ${iconClassName}`}>
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
                <div className="flex items-center gap-3">
                  <Skeleton className="h-8 w-8 rounded-xl" />
                  <Skeleton className="h-3.5 w-20" />
                </div>
                <Skeleton className="h-4 w-8" />
              </div>
            ))}
          </div>
        ) : (
          <>
            <div className="divide-y divide-border/40">
              <SnapshotRow
                icon={ArrowDownToLine}
                label="Arrivals"
                value={data?.arrivals ?? 0}
                iconClassName="bg-gradient-to-br from-blue-500/10 to-blue-600/10 text-blue-600 dark:from-blue-500/20 dark:to-blue-600/20 dark:text-blue-400"
              />
              <SnapshotRow
                icon={ArrowUpFromLine}
                label="Departures"
                value={data?.departures ?? 0}
                iconClassName="bg-gradient-to-br from-orange-500/10 to-orange-600/10 text-orange-600 dark:from-orange-500/20 dark:to-orange-600/20 dark:text-orange-400"
              />
              <SnapshotRow
                icon={BedDouble}
                label="Stay-overs"
                value={data?.stay_overs ?? 0}
                iconClassName="bg-gradient-to-br from-emerald-500/10 to-emerald-600/10 text-emerald-600 dark:from-emerald-500/20 dark:to-emerald-600/20 dark:text-emerald-400"
              />
              <SnapshotRow
                icon={UserX}
                label="No-shows"
                value={data?.no_shows ?? 0}
                iconClassName="bg-gradient-to-br from-red-500/10 to-red-600/10 text-red-600 dark:from-red-500/20 dark:to-red-600/20 dark:text-red-400"
              />
            </div>
            <div className="mt-4">
              <div className="mb-1.5 flex items-center justify-between text-xs text-muted-foreground">
                <span>Occupancy</span>
                <span className="font-semibold text-foreground">
                  {data?.occupied_rooms ?? 0} / {data?.total_rooms ?? 0} rooms
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-muted/50">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-500 dark:shadow-[0_0_8px_hsl(var(--primary)/0.4)]"
                  style={{ width: `${data?.occupancy_pct ?? 0}%` }}
                />
              </div>
              <p className="mt-1 text-right text-xs font-medium text-primary">{(data?.occupancy_pct ?? 0).toFixed(1)}%</p>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
