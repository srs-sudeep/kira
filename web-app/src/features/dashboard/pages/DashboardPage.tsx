import { formatCurrency } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import { useQuery } from '@tanstack/react-query'
import { BanknoteIcon, BedDouble, CalendarDays, TrendingDown } from 'lucide-react'
import { BookingSourcePie } from '../components/BookingSourcePie'
import { ChannelHealthPanel } from '../components/ChannelHealthPanel'
import { KpiCard } from '../components/KpiCard'
import { OccupancyChart } from '../components/OccupancyChart'
import { RecentBookings } from '../components/RecentBookings'
import { TodaySnapshot } from '../components/TodaySnapshot'
import dashboardService from '../services/dashboard-service'

function greeting(): string {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)

  const { data: kpi, isLoading: kpiLoading } = useQuery({
    queryKey: ['dashboard', 'kpi-summary', 30],
    queryFn: () => dashboardService.getKpiSummary(30),
  })

  const firstName = user?.full_name?.split(' ')[0] ?? 'there'

  return (
    <div className="relative -mx-4 -mt-4 min-h-[calc(100vh-3.5rem)] px-4 pb-6 pt-4 sm:-mx-6 sm:px-6">
      {/* Subtle page backdrop — soft gradients behind dashboard content */}
      <div
        className="pointer-events-none absolute inset-0 overflow-hidden rounded-b-2xl"
        aria-hidden
      >
        <div className="absolute -left-24 top-0 h-72 w-72 rounded-full bg-primary/8 blur-3xl" />
        <div className="absolute -right-20 top-32 h-64 w-64 rounded-full bg-accent-500/6 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-48 w-96 -translate-x-1/2 rounded-full bg-primary/5 blur-3xl" />
        <div className="absolute inset-0 opacity-[0.4] [background-image:radial-gradient(circle_at_1px_1px,hsl(var(--border)/0.35)_1px,transparent_0)] [background-size:28px_28px] dark:opacity-[0.15]" />
      </div>

      <div className="relative space-y-6">
        <div className="flex items-start justify-between gap-4 mb-8">
          <div className="min-w-0">
            <h1 className="text-2xl font-bold tracking-tight">
              <span className="bg-gradient-to-r from-foreground via-foreground/85 to-foreground/55 bg-clip-text text-transparent">
                {greeting()}, {firstName}
              </span>
            </h1>
            <p className="mt-1.5 text-sm text-muted-foreground/75 leading-relaxed">
              {kpi?.period_label ?? 'Last 30 days overview'}
            </p>
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <KpiCard
            title="Total Reservations"
            value={kpi?.total_reservations ?? '—'}
            change={kpi?.reservations_change_pct}
            icon={CalendarDays}
            iconClassName="bg-primary/10 dark:bg-primary/20"
            isLoading={kpiLoading}
          />
          <KpiCard
            title="Total Revenue"
            value={kpi?.total_revenue !== undefined ? formatCurrency(kpi.total_revenue) : '—'}
            change={kpi?.revenue_change_pct}
            icon={BanknoteIcon}
            iconClassName="bg-emerald-500/10 dark:bg-emerald-500/20"
            isLoading={kpiLoading}
          />
          <KpiCard
            title="Occupancy Rate"
            value={kpi?.occupancy_rate !== undefined ? `${kpi.occupancy_rate.toFixed(1)}%` : '—'}
            change={kpi?.occupancy_change_pct}
            icon={BedDouble}
            iconClassName="bg-sky-500/10 dark:bg-sky-500/20"
            isLoading={kpiLoading}
          />
          <KpiCard
            title="Cancellation Rate"
            value={kpi?.cancellation_rate !== undefined ? `${kpi.cancellation_rate.toFixed(1)}%` : '—'}
            change={kpi?.cancellation_change_pct}
            icon={TrendingDown}
            iconClassName="bg-red-500/10 dark:bg-red-500/20"
            isLoading={kpiLoading}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <OccupancyChart />
          </div>
          <TodaySnapshot />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <BookingSourcePie />
          <ChannelHealthPanel />
          <div className="hidden lg:col-span-1 lg:block" />
        </div>

        <RecentBookings />
      </div>
    </div>
  )
}
