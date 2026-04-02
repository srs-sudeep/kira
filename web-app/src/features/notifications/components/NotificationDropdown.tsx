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
import { Separator } from '@/components/ui/separator'
import { cn, formatRelativeTime } from '@/lib/utils'
import { ROUTES } from '@/router/routes'
import { QUERY_KEYS } from '@/config/constants'
import notificationsService from '../services/notifications-service'
import type { Notification, NotificationType } from '@/types/notification'

const TYPE_ICONS: Record<NotificationType, React.ElementType> = {
  reservation_created:  BookOpen,
  reservation_modified: Pencil,
  reservation_cancelled: XCircle,
  channel_sync_failed:  AlertTriangle,
  channel_sync_success: CheckCircle2,
  low_availability:     AlertCircle,
  rate_update:          TrendingUp,
  system:               Bell,
}

const TYPE_COLOR: Record<NotificationType, string> = {
  reservation_created:  'text-brand-600 bg-brand-50 dark:bg-brand-950/50',
  reservation_modified: 'text-blue-600 bg-blue-50 dark:bg-blue-950/50',
  reservation_cancelled:'text-destructive bg-red-50 dark:bg-red-950/50',
  channel_sync_failed:  'text-destructive bg-red-50 dark:bg-red-950/50',
  channel_sync_success: 'text-accent-600 bg-accent-50 dark:bg-accent-950/50',
  low_availability:     'text-orange-600 bg-orange-50 dark:bg-orange-950/50',
  rate_update:          'text-violet-600 bg-violet-50 dark:bg-violet-950/50',
  system:               'text-muted-foreground bg-muted',
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
    // Route based on notification type
    if (n.type === 'reservation_created' || n.type === 'reservation_modified' || n.type === 'reservation_cancelled') {
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
    <div className="w-80 overflow-hidden rounded-xl border bg-card shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <p className="font-semibold text-sm text-foreground">Notifications</p>
          {unread.length > 0 && (
            <span className="rounded-full bg-brand-600 px-1.5 py-0.5 text-[10px] font-bold text-white">
              {unread.length}
            </span>
          )}
        </div>
        {unread.length > 0 && (
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1 text-xs"
            onClick={() => markAllMutation.mutate()}
            disabled={markAllMutation.isPending}
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Mark all read
          </Button>
        )}
      </div>

      {/* List */}
      <div className="max-h-80 overflow-y-auto">
        {isLoading ? (
          <div className="space-y-3 p-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <div className="h-8 w-8 shrink-0 animate-pulse rounded-full bg-muted" />
                <div className="flex-1 space-y-1.5">
                  <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
                  <div className="h-3 w-1/2 animate-pulse rounded bg-muted" />
                </div>
              </div>
            ))}
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
            <Bell className="h-6 w-6 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground">All caught up!</p>
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
                      'flex w-full items-start gap-3 px-4 py-3 text-left transition-colors',
                      'hover:bg-muted/50',
                      !n.is_read && 'bg-brand-50/50 dark:bg-brand-950/20',
                    )}
                    onClick={() => handleNotificationClick(n)}
                  >
                    <div
                      className={cn(
                        'mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
                        colorClass,
                      )}
                    >
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p
                          className={cn(
                            'text-xs leading-snug',
                            !n.is_read
                              ? 'font-semibold text-foreground'
                              : 'text-foreground',
                          )}
                        >
                          {n.title}
                        </p>
                        {!n.is_read && (
                          <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />
                        )}
                      </div>
                      <p className="mt-0.5 line-clamp-2 text-[11px] text-muted-foreground">
                        {n.body}
                      </p>
                      <p className="mt-1 text-[10px] text-muted-foreground/70">
                        {formatRelativeTime(n.created_at)}
                      </p>
                    </div>
                  </button>
                  <Separator className="opacity-50" />
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="border-t px-4 py-2">
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-xs text-brand-600 hover:text-brand-700"
          onClick={() => { navigate(ROUTES.NOTIFICATIONS); onClose() }}
        >
          View all notifications
        </Button>
      </div>
    </div>
  )
}
