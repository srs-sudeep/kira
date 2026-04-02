import { useQuery } from '@tanstack/react-query'
import {
  CalendarDays,
  BanknoteIcon,
  BedDouble,
  TrendingDown,
} from 'lucide-react'
import { PageHeader } from '@/components/shared/PageHeader'
import { useAuthStore } from '@/stores/auth-store'
import { formatCurrency } from '@/lib/utils'
import { KpiCard } from '../components/KpiCard'
import { TodaySnapshot } from '../components/TodaySnapshot'
import { ChannelHealthPanel } from '../components/ChannelHealthPanel'
import { RecentBookings } from '../components/RecentBookings'
import { OccupancyChart } from '../components/OccupancyChart'
import { BookingSourcePie } from '../components/BookingSourcePie'
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
    <div className="space-y-6">
      <PageHeader
        title={`${greeting()}, ${firstName}`}
        description={kpi?.period_label ?? 'Last 30 days overview'}
      />

      {/* KPI cards row */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          title="Total Reservations"
          value={kpi?.total_reservations ?? '—'}
          change={kpi?.reservations_change_pct}
          icon={CalendarDays}
          iconClassName="bg-brand-50 dark:bg-brand-950"
          isLoading={kpiLoading}
        />
        <KpiCard
          title="Total Revenue"
          value={
            kpi?.total_revenue !== undefined
              ? formatCurrency(kpi.total_revenue)
              : '—'
          }
          change={kpi?.revenue_change_pct}
          icon={BanknoteIcon}
          iconClassName="bg-accent-50 dark:bg-accent-950"
          isLoading={kpiLoading}
        />
        <KpiCard
          title="Occupancy Rate"
          value={
            kpi?.occupancy_rate !== undefined
              ? `${kpi.occupancy_rate.toFixed(1)}%`
              : '—'
          }
          change={kpi?.occupancy_change_pct}
          icon={BedDouble}
          iconClassName="bg-sky-50 dark:bg-sky-950"
          isLoading={kpiLoading}
        />
        <KpiCard
          title="Cancellation Rate"
          value={
            kpi?.cancellation_rate !== undefined
              ? `${kpi.cancellation_rate.toFixed(1)}%`
              : '—'
          }
          change={kpi?.cancellation_change_pct}
          icon={TrendingDown}
          iconClassName="bg-red-50 dark:bg-red-950"
          isLoading={kpiLoading}
        />
      </div>

      {/* Middle row: charts + side panels */}
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Occupancy chart — spans 2 cols */}
        <div className="lg:col-span-2">
          <OccupancyChart />
        </div>

        {/* Today snapshot */}
        <TodaySnapshot />
      </div>

      {/* Bottom row: pie + channel health + recent bookings */}
      <div className="grid gap-4 lg:grid-cols-3">
        <BookingSourcePie />
        <ChannelHealthPanel />

        {/* Recent bookings spans full width on mobile, 1 col on lg */}
        <div className="lg:col-span-1 hidden lg:block" />
      </div>

      {/* Recent bookings full-width */}
      <RecentBookings />
    </div>
  )
}
