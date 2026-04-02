import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  LogIn,
  LogOut,
  UserX,
  XCircle,
  Hash,
  CalendarDays,
  BedDouble,
  Radio,
  Users,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { PageHeader } from '@/components/shared/PageHeader'
import { LoadingState } from '@/components/shared/LoadingState'
import { ErrorState } from '@/components/shared/ErrorState'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { CurrencyDisplay } from '@/components/shared/CurrencyDisplay'
import { GuestProfileCard } from '../components/GuestProfileCard'
import { ReservationNotes } from '../components/ReservationNotes'
import { CancelReservationDialog } from '../components/CancelReservationDialog'
import { ROUTES } from '@/router/routes'
import { OTA_CHANNEL_LABELS } from '@/config/constants'
import { formatDate, formatNights } from '@/lib/utils'
import reservationsService from '../services/reservations-service'

type QuickAction = 'check_in' | 'check_out' | 'no_show'

const ACTION_CONFIG: Record<
  QuickAction,
  {
    label: string
    loadingLabel: string
    icon: React.ElementType
    variant: 'default' | 'destructive' | 'outline'
    allowedStatuses: string[]
  }
> = {
  check_in: {
    label: 'Check In',
    loadingLabel: 'Checking in…',
    icon: LogIn,
    variant: 'default',
    allowedStatuses: ['confirmed'],
  },
  check_out: {
    label: 'Check Out',
    loadingLabel: 'Checking out…',
    icon: LogOut,
    variant: 'outline',
    allowedStatuses: ['checked_in'],
  },
  no_show: {
    label: 'Mark No-Show',
    loadingLabel: 'Marking…',
    icon: UserX,
    variant: 'destructive',
    allowedStatuses: ['confirmed'],
  },
}

export default function ReservationDetailPage() {
  const { reservationId } = useParams<{ reservationId: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [cancelOpen, setCancelOpen] = useState(false)

  const {
    data: reservation,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['reservations', reservationId],
    queryFn: () => reservationsService.get(reservationId!),
    enabled: !!reservationId,
  })

  const quickActionMutation = useMutation({
    mutationFn: (action: QuickAction) => {
      switch (action) {
        case 'check_in': return reservationsService.checkIn(reservationId!)
        case 'check_out': return reservationsService.checkOut(reservationId!)
        case 'no_show': return reservationsService.markNoShow(reservationId!)
      }
    },
    onSuccess(updated) {
      qc.setQueryData(['reservations', reservationId], updated)
      qc.invalidateQueries({ queryKey: ['reservations'] })
      toast.success(`Status updated to ${updated.status.replace('_', ' ')}`)
    },
  })

  if (isLoading) return <LoadingState message="Loading reservation…" />
  if (isError || !reservation)
    return <ErrorState message="Reservation not found." onRetry={refetch} />

  const nights = formatNights(reservation.check_in_date, reservation.check_out_date)

  return (
    <>
      <PageHeader
        title={`Reservation ${reservation.booking_reference}`}
        description={
          OTA_CHANNEL_LABELS[reservation.channel] ?? reservation.channel
        }
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(ROUTES.RESERVATIONS)}
          >
            <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
            Back
          </Button>
        }
      />

      <div className="grid gap-5 lg:grid-cols-3">
        {/* ── Left: Booking Details (2/3) ──────────────────────────────────── */}
        <div className="space-y-5 lg:col-span-2">
          {/* Booking info card */}
          <Card>
            <CardHeader className="flex-row items-center justify-between pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Booking Details
              </CardTitle>
              <StatusBadge status={reservation.status} />
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-x-6 gap-y-4 text-sm sm:grid-cols-3">
                <div>
                  <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Hash className="h-3 w-3" /> Reference
                  </p>
                  <p className="mt-0.5 font-mono font-semibold text-foreground">
                    {reservation.booking_reference}
                  </p>
                </div>
                <div>
                  <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Radio className="h-3 w-3" /> Channel
                  </p>
                  <p className="mt-0.5 font-medium text-foreground">
                    {OTA_CHANNEL_LABELS[reservation.channel] ?? reservation.channel}
                  </p>
                  <p className="text-[10px] text-muted-foreground font-mono">
                    {reservation.channel_booking_id}
                  </p>
                </div>
                <div>
                  <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Users className="h-3 w-3" /> Guests
                  </p>
                  <p className="mt-0.5 text-foreground">
                    {reservation.adults} adult{reservation.adults !== 1 ? 's' : ''}
                    {reservation.children > 0 &&
                      `, ${reservation.children} child${reservation.children !== 1 ? 'ren' : ''}`}
                  </p>
                </div>
                <div>
                  <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <CalendarDays className="h-3 w-3" /> Check-in
                  </p>
                  <p className="mt-0.5 font-medium text-foreground">
                    {formatDate(reservation.check_in_date)}
                  </p>
                </div>
                <div>
                  <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <CalendarDays className="h-3 w-3" /> Check-out
                  </p>
                  <p className="mt-0.5 font-medium text-foreground">
                    {formatDate(reservation.check_out_date)}{' '}
                    <span className="text-xs text-muted-foreground">({nights}n)</span>
                  </p>
                </div>
                <div>
                  <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <BedDouble className="h-3 w-3" /> Room / Rate
                  </p>
                  <p className="mt-0.5 font-medium text-foreground">
                    {reservation.room_type_name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {reservation.rate_plan_name}
                  </p>
                </div>
              </div>

              <Separator className="my-4" />

              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">Total Amount</p>
                <CurrencyDisplay
                  amount={reservation.total_amount}
                  currency={reservation.currency}
                  size="lg"
                />
              </div>

              {reservation.special_requests && (
                <>
                  <Separator className="my-4" />
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">Special Requests</p>
                    <p className="mt-1 text-sm text-foreground">{reservation.special_requests}</p>
                  </div>
                </>
              )}

              {reservation.cancellation_reason && (
                <>
                  <Separator className="my-4" />
                  <div>
                    <p className="text-xs font-medium text-destructive">Cancellation Reason</p>
                    <p className="mt-1 text-sm text-foreground">
                      {reservation.cancellation_reason}
                    </p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Notes */}
          <Card>
            <CardContent className="pt-6">
              <ReservationNotes reservationId={reservation.id} />
            </CardContent>
          </Card>
        </div>

        {/* ── Right: Guest + Actions (1/3) ─────────────────────────────────── */}
        <div className="space-y-4">
          <GuestProfileCard guest={reservation.guest} />

          {/* Quick actions */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {(Object.entries(ACTION_CONFIG) as [QuickAction, typeof ACTION_CONFIG[QuickAction]][]).map(
                ([action, cfg]) => {
                  const allowed = cfg.allowedStatuses.includes(reservation.status)
                  if (!allowed) return null
                  return (
                    <Button
                      key={action}
                      variant={cfg.variant}
                      size="sm"
                      className="w-full justify-start gap-2"
                      disabled={quickActionMutation.isPending}
                      onClick={() => quickActionMutation.mutate(action)}
                    >
                      <cfg.icon className="h-4 w-4" />
                      {quickActionMutation.isPending &&
                      quickActionMutation.variables === action
                        ? cfg.loadingLabel
                        : cfg.label}
                    </Button>
                  )
                },
              )}

              {['confirmed', 'pending'].includes(reservation.status) && (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full justify-start gap-2 text-destructive hover:text-destructive"
                  onClick={() => setCancelOpen(true)}
                >
                  <XCircle className="h-4 w-4" />
                  Cancel Reservation
                </Button>
              )}

              {['cancelled', 'checked_out', 'no_show'].includes(reservation.status) && (
                <p className="text-center text-xs text-muted-foreground py-2">
                  No actions available for this status.
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      <CancelReservationDialog
        open={cancelOpen}
        onOpenChange={setCancelOpen}
        reservationId={reservation.id}
        bookingReference={reservation.booking_reference}
      />
    </>
  )
}
