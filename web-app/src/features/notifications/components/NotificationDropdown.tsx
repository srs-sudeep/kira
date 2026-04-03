import type { ElementType } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  BookOpen,
  Pencil,
  XCircle,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Bell,
  CheckCheck,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn, formatRelativeTime } from '@/lib/utils'
import { ROUTES } from '@/router/routes'
import { QUERY_KEYS } from '@/config/constants'
import notificationsService from '../services/notifications-service'
import type { Notification, NotificationType } from '@/types/notification'

const TYPE_ICONS: Record<NotificationType, ElementType> = {
  reservation_created: BookOpen,
  reservation_modified: Pencil,
  reservation_cancelled: XCircle,
  channel_sync_failed: AlertTriangle,
  channel_sync_success: CheckCircle2,
  low_availability: AlertCircle,
  rate_update: TrendingUp,
  system: Bell,
}

const TYPE_COLOR: Record<NotificationType, string> = {
  reservation_created: 'text-primary bg-primary/12 border-primary/10',
  reservation_modified: 'text-blue-600 bg-blue-500/[0.1] border-blue-500/15 dark:text-blue-400',
  reservation_cancelled: 'text-red-600 bg-red-500/[0.1] border-red-500/15 dark:text-red-400',
  channel_sync_failed: 'text-red-600 bg-red-500/[0.1] border-red-500/15 dark:text-red-400',
  channel_sync_success: 'text-emerald-600 bg-emerald-500/[0.1] border-emerald-500/15 dark:text-emerald-400',
  low_availability: 'text-orange-600 bg-orange-500/[0.1] border-orange-500/15 dark:text-orange-400',
  rate_update: 'text-violet-600 bg-violet-500/[0.1] border-violet-500/15 dark:text-violet-400',
  system: 'text-muted-foreground bg-muted/40 border-border/30',
}

interface Props {
  onClose: () => void
}

export function NotificationDropdown({ onClose }: Props) {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: notifications = [], isLoading } = useQuery({
    queryKey: ['notifications', 'latest'],
    queryFn: () => notificationsService.getLatest(5),
  })

  const markAllMutation = useMutation({
    mutationFn: notificationsService.markAllRead,
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS.UNREAD_COUNT })
      qc.invalidateQueries({ queryKey: ['notifications', 'latest'] })
    },
  })

  const markOneMutation = useMutation({
    mutationFn: (id: string) => notificationsService.markRead([id]),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS.UNREAD_COUNT })
      qc.invalidateQueries({ queryKey: ['notifications', 'latest'] })
    },
  })

  function handleNotificationClick(n: Notification) {
    if (!n.is_read) markOneMutation.mutate(n.id)
    onClose()
    if (
      n.type === 'reservation_created' ||
      n.type === 'reservation_modified' ||
      n.type === 'reservation_cancelled'
    ) {
      const id = (n.data as { reservation_id?: string })?.reservation_id
      if (id) navigate(ROUTES.RESERVATION_DETAIL.replace(':reservationId', id))
      else navigate(ROUTES.RESERVATIONS)
    } else if (n.type === 'channel_sync_failed' || n.type === 'channel_sync_success') {
      const id = (n.data as { channel_id?: string })?.channel_id
      if (id) navigate(ROUTES.CHANNEL_DETAIL.replace(':channelId', id))
      else navigate(ROUTES.CHANNELS)
    } else {
      navigate(ROUTES.NOTIFICATIONS)
    }
  }

  const unread = notifications.filter((n) => !n.is_read)

  return (
    <div className="w-80 overflow-hidden rounded-xl border border-border/25 bg-popover/85 glass shadow-2xl backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-border/25 px-4 py-3 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold tracking-tight text-foreground">Notifications</p>
          {unread.length > 0 && (
            <span className="rounded-full bg-primary/90 px-1.5 py-0.5 text-[10px] font-bold text-primary-foreground shadow-sm">
              {unread.length}
            </span>
          )}
        </div>
        {unread.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1 text-xs text-muted-foreground hover:text-foreground"
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Mark all read
          </Button>
        )}
      </div>
      <div className="max-h-80 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-3 p-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-9 w-9 shrink-0 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-3 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                  <Skeleton className="h-2.5 w-20" />
                </div>
              </div>
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
            <Bell className="h-7 w-7 text-muted-foreground/25" />
            <p className="text-sm font-medium text-muted-foreground">All caught up</p>
            <p className="text-xs text-muted-foreground/65">No new notifications</p>
          </div>
        ) : (
          <ul>
            {notifications.map((n) => {
              const Icon = TYPE_ICONS[n.type] ?? Bell
              const colorClass = TYPE_COLOR[n.type] ?? TYPE_COLOR.system
              return (
                <li key={n.id}>
                  <button
                    type="button"
                    className={cn(
                      'flex w-full items-start gap-3 border-b border-border/20 px-4 py-3.5 text-left transition-colors last:border-b-0 hover:bg-muted/25',
                      !n.is_read && 'bg-primary/[0.04]',
                    )}
                    onClick={() => handleNotificationClick(n)}
                  >
                    <div
                      className={cn(
                        'mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border',
                        colorClass,
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <p
                          className={cn(
                            'text-[13px] leading-snug',
                            !n.is_read ? 'font-semibold text-foreground' : 'font-medium text-foreground/85',
                          )}
                        >
                          {n.title}
                        </p>
                        {!n.is_read && (
                          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary shadow-[0_0_8px_hsl(var(--primary)/0.55)]" />
                        )}
                      </div>
                      <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-muted-foreground/75">
                        {n.body}
                      </p>
                      <p className="mt-1.5 text-[10px] font-medium uppercase tracking-wide text-muted-foreground/45">
                        {formatRelativeTime(n.created_at)}
                      </p>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>
      <div className="border-t border-border/25 bg-muted/[0.06] px-4 py-2 backdrop-blur-sm">
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-xs font-medium text-primary hover:text-primary"
          onClick={() => {
            navigate(ROUTES.NOTIFICATIONS)
            onClose()
          }}
        >
          View all notifications
        </Button>
      </div>
    </div>
  )
}
