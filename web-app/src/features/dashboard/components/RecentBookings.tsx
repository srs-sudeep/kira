import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { type ColumnDef } from '@tanstack/react-table'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { CurrencyDisplay } from '@/components/shared/CurrencyDisplay'
import { DataTable } from '@/components/shared/DataTable'
import { formatDate } from '@/lib/utils'
import { OTA_CHANNEL_LABELS } from '@/config/constants'
import { ROUTES } from '@/router/routes'
import type { Reservation } from '@/types/reservation'
import dashboardService from '../services/dashboard-service'

const columns: ColumnDef<Reservation>[] = [
  {
    accessorKey: 'guest',
    header: 'Guest',
    cell: ({ row }) => {
      const guest = row.original.guest
      return (
        <div>
          <p className="text-sm font-medium text-foreground">
            {guest.first_name} {guest.last_name}
          </p>
          <p className="text-xs text-muted-foreground">{guest.email}</p>
        </div>
      )
    },
  },
  {
    accessorKey: 'room_type_name',
    header: 'Room',
    cell: ({ row }) => (
      <div>
        <p className="text-sm text-foreground">{row.original.room_type_name}</p>
        <p className="text-xs text-muted-foreground">{row.original.rate_plan_name}</p>
      </div>
    ),
  },
  {
    accessorKey: 'channel',
    header: 'Source',
    cell: ({ getValue }) => (
      <span className="text-sm text-muted-foreground">
        {OTA_CHANNEL_LABELS[getValue<string>()] ?? getValue<string>()}
      </span>
    ),
  },
  {
    accessorKey: 'check_in_date',
    header: 'Check-in',
    cell: ({ getValue }) => (
      <span className="text-sm tabular-nums">{formatDate(getValue<string>())}</span>
    ),
  },
  {
    accessorKey: 'total_amount',
    header: 'Amount',
    cell: ({ row }) => (
      <CurrencyDisplay
        amount={row.original.total_amount}
        currency={row.original.currency}
        size="sm"
      />
    ),
  },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ getValue }) => <StatusBadge status={getValue<string>()} />,
  },
]

export function RecentBookings() {
  const navigate = useNavigate()

  const { data = [], isLoading } = useQuery({
    queryKey: ['dashboard', 'recent-bookings'],
    queryFn: () => dashboardService.getRecentBookings(5),
  })

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="text-base font-semibold">Recent Bookings</CardTitle>
        <Button
          variant="ghost"
          size="sm"
          className="text-xs"
          onClick={() => navigate(ROUTES.RESERVATIONS)}
        >
          View all
        </Button>
      </CardHeader>
      <CardContent>
        <DataTable
          columns={columns}
          data={data}
          isLoading={isLoading}
        />
      </CardContent>
    </Card>
  )
}
