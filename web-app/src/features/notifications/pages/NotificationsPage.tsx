import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Bell, CheckCheck, Trash2, Filter, BookOpen, Pencil,
  XCircle, AlertTriangle, CheckCircle2, AlertCircle, TrendingUp,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn, formatRelativeTime } from '@/lib/utils'
import { QUERY_KEYS } from '@/config/constants'
import notificationsService from '../services/notifications-service'
import type { Notification, NotificationType, NotificationPreferences } from '@/types/notification'

// ── Icon / colour maps ────────────────────────────────────────────────────────

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

const TYPE_LABELS: Record<NotificationType, string> = {
  reservation_created:  'Reservation Created',
  reservation_modified: 'Reservation Modified',
  reservation_cancelled:'Reservation Cancelled',
  channel_sync_failed:  'Sync Failed',
  channel_sync_success: 'Sync Success',
  low_availability:     'Low Availability',
  rate_update:          'Rate Update',
  system:               'System',
}

// ── Preference labels ─────────────────────────────────────────────────────────

const PREF_LABELS: Array<{ key: keyof NotificationPreferences; label: string; description: string }> = [
  { key: 'email_reservation_created',   label: 'New Reservations',    description: 'Email when a new booking arrives' },
  { key: 'email_reservation_modified',  label: 'Reservation Changes', description: 'Email when a booking is modified' },
  { key: 'email_reservation_cancelled', label: 'Cancellations',       description: 'Email when a booking is cancelled' },
  { key: 'email_channel_sync_failed',   label: 'Sync Failures',       description: 'Email when a channel sync fails' },
  { key: 'email_low_availability',      label: 'Low Availability',    description: 'Email when availability drops below threshold' },
  { key: 'in_app_reservation_created',  label: 'New Reservations',    description: 'In-app alert for new bookings' },
  { key: 'in_app_reservation_modified', label: 'Reservation Changes', description: 'In-app alert for modifications' },
  { key: 'in_app_channel_sync_failed',  label: 'Sync Failures',       description: 'In-app alert for sync failures' },
  { key: 'in_app_low_availability',     label: 'Low Availability',    description: 'In-app alert for low availability' },
  { key: 'in_app_rate_update',          label: 'Rate Updates',        description: 'In-app alert for rate changes' },
]

// ── Filter bar ────────────────────────────────────────────────────────────────

interface Filters {
  type: NotificationType | 'all'
  is_read: 'all' | 'unread' | 'read'
}

function FilterBar({ filters, onChange }: { filters: Filters; onChange: (f: Filters) => void }) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      <Filter className="h-4 w-4 text-muted-foreground" />
      <Select
        value={filters.type}
        onValueChange={(v) => onChange({ ...filters, type: v as Filters['type'] })}
      >
        <SelectTrigger className="h-8 w-48 text-xs">
          <SelectValue placeholder="All types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All types</SelectItem>
          {(Object.keys(TYPE_LABELS) as NotificationType[]).map((t) => (
            <SelectItem key={t} value={t}>{TYPE_LABELS[t]}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={filters.is_read}
        onValueChange={(v) => onChange({ ...filters, is_read: v as Filters['is_read'] })}
      >
        <SelectTrigger className="h-8 w-36 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All</SelectItem>
          <SelectItem value="unread">Unread</SelectItem>
          <SelectItem value="read">Read</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}

// ── Notification row ──────────────────────────────────────────────────────────

function NotificationRow({
  n, selected, onSelect, onMarkRead,
}: {
  n: Notification
  selected: boolean
  onSelect: (checked: boolean) => void
  onMarkRead: () => void
}) {
  const Icon = TYPE_ICONS[n.type] ?? Bell
  const colorClass = TYPE_COLOR[n.type] ?? TYPE_COLOR.system

  return (
    <div
      className={cn(
        'flex items-start gap-4 px-4 py-3 transition-colors hover:bg-muted/40 group',
        !n.is_read && 'bg-brand-50/40 dark:bg-brand-950/10',
      )}
    >
      <Checkbox
        checked={selected}
        onCheckedChange={onSelect}
        className="mt-1 shrink-0"
        aria-label={`Select notification: ${n.title}`}
      />
      <div className={cn('mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full', colorClass)}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <p className={cn('truncate text-sm leading-snug', !n.is_read ? 'font-semibold text-foreground' : 'text-foreground')}>
                {n.title}
              </p>
              {!n.is_read && <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-brand-600" />}
              <Badge variant="outline" className="shrink-0 text-[10px]">{TYPE_LABELS[n.type]}</Badge>
            </div>
            <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{n.body}</p>
          </div>
          <div className="flex shrink-0 flex-col items-end gap-1">
            <span className="whitespace-nowrap text-[11px] text-muted-foreground/70">
              {formatRelativeTime(n.created_at)}
            </span>
            {!n.is_read && (
              <button
                type="button"
                className="hidden text-[11px] text-brand-600 hover:underline group-hover:block"
                onClick={onMarkRead}
              >
                Mark read
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Preferences tab ───────────────────────────────────────────────────────────

function PreferencesTab() {
  const qc = useQueryClient()

  const { data: prefs, isLoading } = useQuery({
    queryKey: QUERY_KEYS.NOTIFICATIONS.PREFERENCES,
    queryFn: notificationsService.getPreferences,
  })

  const mutation = useMutation({
    mutationFn: (p: Partial<NotificationPreferences>) => notificationsService.updatePreferences(p),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS.PREFERENCES })
    },
  })

  function toggle(key: keyof NotificationPreferences) {
    if (!prefs) return
    mutation.mutate({ [key]: !prefs[key] })
  }

  const emailPrefs = PREF_LABELS.filter((p) => p.key.startsWith('email_'))
  const inAppPrefs = PREF_LABELS.filter((p) => p.key.startsWith('in_app_'))

  if (isLoading) {
    return (
      <div className="space-y-3 p-6">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center justify-between">
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-5 w-9 rounded-full" />
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="grid gap-6 p-6 md:grid-cols-2">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Email Notifications</CardTitle>
          <CardDescription>Choose which events trigger an email</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {emailPrefs.map(({ key, label, description }) => (
            <div key={key} className="flex items-center justify-between gap-4">
              <div>
                <Label htmlFor={key} className="text-sm font-medium">{label}</Label>
                <p className="text-xs text-muted-foreground">{description}</p>
              </div>
              <Switch
                id={key}
                checked={prefs?.[key] ?? false}
                onCheckedChange={() => toggle(key)}
                disabled={mutation.isPending}
              />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">In-App Notifications</CardTitle>
          <CardDescription>Choose which events show up in the bell</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {inAppPrefs.map(({ key, label, description }) => (
            <div key={key} className="flex items-center justify-between gap-4">
              <div>
                <Label htmlFor={key} className="text-sm font-medium">{label}</Label>
                <p className="text-xs text-muted-foreground">{description}</p>
              </div>
              <Switch
                id={key}
                checked={prefs?.[key] ?? false}
                onCheckedChange={() => toggle(key)}
                disabled={mutation.isPending}
              />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function NotificationsPage() {
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [filters, setFilters] = useState<Filters>({ type: 'all', is_read: 'all' })

  const queryParams = {
    page,
    page_size: 20,
    type: filters.type === 'all' ? undefined : filters.type,
    is_read: filters.is_read === 'all' ? undefined : filters.is_read === 'read',
  }

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.NOTIFICATIONS.LIST(queryParams),
    queryFn: () => notificationsService.list(queryParams),
  })

  const notifications = data?.items ?? []
  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1

  const markReadMutation = useMutation({
    mutationFn: (ids: string[]) => notificationsService.markRead(ids),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS.UNREAD_COUNT })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS.LIST })
      setSelected(new Set())
    },
  })

  const markAllMutation = useMutation({
    mutationFn: notificationsService.markAllRead,
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS.UNREAD_COUNT })
      qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS.LIST })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (ids: string[]) => notificationsService.bulkDelete(ids),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.NOTIFICATIONS.LIST })
      setSelected(new Set())
    },
  })

  function toggleSelect(id: string, checked: boolean) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (checked) { next.add(id) } else { next.delete(id) }
      return next
    })
  }

  const allSelected = notifications.length > 0 && selected.size === notifications.length
  const someSelected = selected.size > 0

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Notifications</h1>
          <p className="text-sm text-muted-foreground">
            Stay on top of reservations, channel activity, and system alerts
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={() => markAllMutation.mutate()}
          disabled={markAllMutation.isPending}
        >
          <CheckCheck className="h-4 w-4" />
          Mark all read
        </Button>
      </div>

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Notifications</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          <Card className="overflow-hidden">
            {/* Toolbar */}
            <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
              <FilterBar filters={filters} onChange={(f) => { setFilters(f); setPage(1) }} />
              {someSelected && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">{selected.size} selected</span>
                  <Button
                    variant="outline" size="sm" className="h-7 gap-1 text-xs"
                    onClick={() => markReadMutation.mutate(Array.from(selected))}
                    disabled={markReadMutation.isPending}
                  >
                    <CheckCheck className="h-3.5 w-3.5" /> Mark read
                  </Button>
                  <Button
                    variant="outline" size="sm"
                    className="h-7 gap-1 text-xs text-destructive hover:text-destructive"
                    onClick={() => deleteMutation.mutate(Array.from(selected))}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-3.5 w-3.5" /> Delete
                  </Button>
                </div>
              )}
            </div>

            {/* Select-all */}
            <div className="flex items-center gap-3 border-b bg-muted/30 px-4 py-2">
              <Checkbox
                checked={allSelected}
                onCheckedChange={(c) => {
                  setSelected(c ? new Set(notifications.map((n) => n.id)) : new Set())
                }}
                aria-label="Select all"
              />
              <span className="text-xs text-muted-foreground">
                {allSelected ? 'Deselect all' : 'Select all on this page'}
              </span>
            </div>

            {isLoading ? (
              <div className="divide-y">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="flex items-start gap-4 px-4 py-3">
                    <Skeleton className="mt-1 h-4 w-4 rounded" />
                    <Skeleton className="h-9 w-9 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-2/3" />
                      <Skeleton className="h-3 w-1/2" />
                    </div>
                  </div>
                ))}
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
                <Bell className="h-10 w-10 text-muted-foreground/30" />
                <p className="font-medium text-muted-foreground">No notifications</p>
                <p className="text-sm text-muted-foreground">
                  {filters.type !== 'all' || filters.is_read !== 'all'
                    ? 'Try adjusting your filters'
                    : "You're all caught up!"}
                </p>
              </div>
            ) : (
              <div className="divide-y">
                {notifications.map((n) => (
                  <NotificationRow
                    key={n.id}
                    n={n}
                    selected={selected.has(n.id)}
                    onSelect={(c) => toggleSelect(n.id, !!c)}
                    onMarkRead={() => markReadMutation.mutate([n.id])}
                  />
                ))}
              </div>
            )}

            {totalPages > 1 && (
              <>
                <Separator />
                <div className="flex items-center justify-between px-4 py-3">
                  <span className="text-xs text-muted-foreground">Page {page} of {totalPages}</span>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                      Previous
                    </Button>
                    <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                      Next
                    </Button>
                  </div>
                </div>
              </>
            )}
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="mt-4">
          <PreferencesTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
