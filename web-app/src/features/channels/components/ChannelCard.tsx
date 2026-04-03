import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, MoreHorizontal, ExternalLink, Power, PowerOff } from 'lucide-react'
import { toast } from 'sonner'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn, formatRelativeTime } from '@/lib/utils'
import { ChannelHealthBadge } from './ChannelHealthBadge'
import { ROUTES } from '@/router/routes'
import { OTA_CHANNEL_LABELS } from '@/config/constants'
import channelsService from '../services/channels-service'
import type { Channel } from '@/types/channel'

const OTA_COLORS: Record<string, string> = {
  booking_com: 'from-blue-500 to-blue-700',
  expedia: 'from-yellow-400 to-orange-500',
  make_my_trip: 'from-red-500 to-red-700',
}

const OTA_INITIALS: Record<string, string> = {
  booking_com: 'B.',
  expedia: 'EX',
  make_my_trip: 'MMT',
}

interface ChannelCardProps {
  channel: Channel
}

export function ChannelCard({ channel }: ChannelCardProps) {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const syncMutation = useMutation({
    mutationFn: () => channelsService.triggerSync(channel.id, 'full_sync'),
    onSuccess() {
      toast.success('Sync triggered')
      qc.invalidateQueries({ queryKey: ['channels', channel.id] })
    },
  })

  const toggleMutation = useMutation({
    mutationFn: () => channelsService.update(channel.id, { is_active: !channel.is_active }),
    onSuccess() {
      qc.invalidateQueries({ queryKey: ['channels'] })
      toast.success(channel.is_active ? 'Channel deactivated' : 'Channel activated')
    },
  })

  const gradientClass = OTA_COLORS[channel.ota] ?? 'from-slate-500 to-slate-700'

  return (
    <Card
      className={cn(
        'group overflow-hidden border-border/40 bg-card/75 glass shadow-lg hover-lift',
        'transition-[transform,box-shadow] duration-200',
      )}
    >
      <div
        className={cn(
          'relative flex h-20 items-center justify-between px-4',
          'bg-gradient-to-r',
          gradientClass,
          'border-b border-white/10 shadow-inner',
        )}
      >
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/10 to-transparent" />
        <div className="relative flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/25 bg-white/15 shadow-lg backdrop-blur-md">
            <span className="text-sm font-bold text-white drop-shadow-sm">
              {OTA_INITIALS[channel.ota] ?? channel.ota.slice(0, 2).toUpperCase()}
            </span>
          </div>
          <div>
            <p className="font-semibold text-white drop-shadow-sm">{channel.display_name}</p>
            <p className="text-xs text-white/75">{OTA_CHANNEL_LABELS[channel.ota] ?? channel.ota}</p>
          </div>
        </div>
        <div
          className="relative opacity-0 transition-opacity group-hover:opacity-100"
          onClick={(e) => e.stopPropagation()}
        >
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-white hover:bg-white/20"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                className="gap-2"
                onClick={() =>
                  navigate(ROUTES.CHANNEL_DETAIL.replace(':channelId', channel.id))
                }
              >
                <ExternalLink className="h-3.5 w-3.5" /> View Details
              </DropdownMenuItem>
              <DropdownMenuItem
                className="gap-2"
                onClick={() => syncMutation.mutate()}
                disabled={syncMutation.isPending || !channel.is_active}
              >
                <RefreshCw
                  className={cn('h-3.5 w-3.5', syncMutation.isPending && 'animate-spin')}
                />
                Trigger Sync
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="gap-2"
                onClick={() => toggleMutation.mutate()}
                disabled={toggleMutation.isPending}
              >
                {channel.is_active ? (
                  <>
                    <PowerOff className="h-3.5 w-3.5 text-destructive" /> Deactivate
                  </>
                ) : (
                  <>
                    <Power className="h-3.5 w-3.5 text-emerald-600" /> Activate
                  </>
                )}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <CardContent
        className="cursor-pointer bg-muted/5 p-4 backdrop-blur-[2px] dark:bg-muted/10"
        onClick={() => navigate(ROUTES.CHANNEL_DETAIL.replace(':channelId', channel.id))}
      >
        <div className="flex items-center justify-between">
          <ChannelHealthBadge status={channel.sync_status} />
          {!channel.is_active && (
            <Badge variant="secondary" className="border-0 bg-muted/40 text-[11px] backdrop-blur-sm">
              Inactive
            </Badge>
          )}
        </div>
        <div className="mt-3 space-y-1.5 text-xs text-muted-foreground/65">
          <p>
            <span className="font-medium text-foreground/90">Hotel ID:</span>{' '}
            <span className="font-mono text-muted-foreground/80">{channel.hotel_id}</span>
          </p>
          <p>
            {channel.last_synced_at
              ? `Last synced ${formatRelativeTime(channel.last_synced_at)}`
              : 'Never synced'}
          </p>
          {channel.last_sync_error && (
            <p className="truncate text-destructive/90" title={channel.last_sync_error}>
              ⚠ {channel.last_sync_error}
            </p>
          )}
        </div>
      </CardContent>
      <CardFooter className="border-t border-border/30 bg-muted/5 px-4 pb-4 pt-3 dark:bg-muted/[0.08]">
        <Button
          variant="outline"
          size="sm"
          className="w-full gap-1.5 border-border/40 bg-background/50 glass"
          onClick={() => syncMutation.mutate()}
          disabled={syncMutation.isPending || !channel.is_active}
        >
          <RefreshCw className={cn('h-3.5 w-3.5', syncMutation.isPending && 'animate-spin')} />
          {syncMutation.isPending ? 'Syncing…' : 'Sync Now'}
        </Button>
      </CardFooter>
    </Card>
  )
}
