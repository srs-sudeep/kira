import { useNavigate } from 'react-router-dom'
import { type ColumnDef } from '@tanstack/react-table'
import { ExternalLink } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/shared/DataTable'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { CurrencyDisplay } from '@/components/shared/CurrencyDisplay'
import { formatDate, formatNights } from '@/lib/utils'
import { OTA_CHANNEL_LABELS } from '@/config/constants'
import { ROUTES } from '@/router/routes'
import type { Reservation } from '@/types/reservation'

interface Props {
  data: Reservation[]
  isLoading: boolean
  total?: number
  page?: number
  pageSize?: number
  onPageChange?: (page: number) => void
  onPageSizeChange?: (size: number) => void
}

export function ReservationTable({
  data,
  isLoading,
  total,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
}: Props) {
  const navigate = useNavigate()

  const columns: ColumnDef<Reservation>[] = [
    {
      accessorKey: 'booking_reference',
      header: 'Booking Ref',
      cell: ({ row }) => (
        <div>
          <p className="font-mono text-xs font-semibold text-foreground">
            {row.original.booking_reference}
          </p>
          <p className="text-[10px] text-muted-foreground">
            {OTA_CHANNEL_LABELS[row.original.channel] ?? row.original.channel}
          </p>
        </div>
      ),
    },
    {
      accessorKey: 'guest',
      header: 'Guest',
      cell: ({ row }) => {
        const { first_name, last_name, email } = row.original.guest
        return (
          <div>
            <p className="text-sm font-medium text-foreground">
              {first_name} {last_name}
            </p>
            <p className="text-xs text-muted-foreground truncate max-w-[160px]">{email}</p>
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
      accessorKey: 'check_in_date',
      header: 'Check-in',
      cell: ({ getValue }) => (
        <span className="text-sm tabular-nums">{formatDate(getValue<string>())}</span>
      ),
    },
    {
      accessorKey: 'check_out_date',
      header: 'Check-out',
      cell: ({ row }) => (
        <div className="text-sm tabular-nums">
          <span>{formatDate(row.original.check_out_date)}</span>
          <span className="ml-1.5 text-xs text-muted-foreground">
            ({formatNights(row.original.check_in_date, row.original.check_out_date)}n)
          </span>
        </div>
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
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={(e) => {
            e.stopPropagation()
            navigate(
              ROUTES.RESERVATION_DETAIL.replace(':reservationId', row.original.id),
            )
          }}
          aria-label="View details"
        >
          <ExternalLink className="h-3.5 w-3.5" />
        </Button>
      ),
    },
  ]

  return (
    <DataTable
      columns={columns}
      data={data}
      isLoading={isLoading}
      total={total}
      page={page}
      pageSize={pageSize}
      onPageChange={onPageChange}
      onPageSizeChange={onPageSizeChange}
    />
  )
}
