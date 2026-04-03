import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatRelativeTime } from '@/lib/utils'
import { OTA_CHANNEL_LABELS } from '@/config/constants'
import { ROUTES } from '@/router/routes'
import dashboardService from '../services/dashboard-service'

export function ChannelHealthPanel() {
  const navigate = useNavigate()

  const { data = [], isLoading, refetch, isFetching } = useQuery({
    queryKey: ['dashboard', 'channel-health'],
    queryFn: dashboardService.getChannelHealth,
    refetchInterval: 60_000, // auto-refresh every 60 s
  })

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Channel Health
        </CardTitle>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7"
          onClick={() => refetch()}
          disabled={isFetching}
          aria-label="Refresh"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
        </Button>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="h-4 w-32 animate-pulse rounded bg-muted" />
                <div className="h-5 w-16 animate-pulse rounded-full bg-muted" />
              </div>
            ))}
          </div>
        ) : data.length === 0 ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            No channels connected yet.
          </p>
        ) : (
          <ul className="divide-y divide-border">
            {data.map((channel) => (
              <li
                key={channel.channel_id}
                className="flex items-center justify-between py-2.5 cursor-pointer hover:bg-muted/40 -mx-2 px-2 rounded transition-colors"
                onClick={() =>
                  navigate(
                    ROUTES.CHANNEL_DETAIL.replace(':channelId', channel.channel_id),
                  )
                }
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">
                    {channel.display_name ||
                      OTA_CHANNEL_LABELS[channel.ota] ||
                      channel.ota}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {channel.last_synced_at
                      ? `Synced ${formatRelativeTime(channel.last_synced_at)}`
                      : 'Never synced'}
                  </p>
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  {channel.error_count_24h > 0 && (
                    <span className="flex items-center gap-0.5 text-xs text-destructive">
                      <AlertCircle className="h-3 w-3" />
                      {channel.error_count_24h}
                    </span>
                  )}
                  <StatusBadge status={channel.sync_status} />
                </div>
              </li>
            ))}
          </ul>
        )}

        <Button
          variant="ghost"
          size="sm"
          className="mt-3 w-full text-xs"
          onClick={() => navigate(ROUTES.CHANNELS)}
        >
          Manage channels
        </Button>
      </CardContent>
    </Card>
  )
}
