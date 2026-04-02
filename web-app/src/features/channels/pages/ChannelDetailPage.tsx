import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft, RefreshCw, Settings, Map, History, LayoutDashboard,
  Wifi, WifiOff, Trash2,
} from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from '@/components/ui/form'
import { QUERY_KEYS, OTA_CHANNEL_LABELS } from '@/config/constants'
import { ROUTES } from '@/router/routes'
import { formatRelativeTime } from '@/lib/utils'
import channelsService from '../services/channels-service'
import { ChannelHealthBadge } from '../components/ChannelHealthBadge'
import { ChannelMappingTable } from '../components/ChannelMappingTable'
import { SyncLogTable } from '../components/SyncLogTable'

// ── Settings tab schema ───────────────────────────────────────────────────────

const settingsSchema = z.object({
  display_name: z.string().min(1, 'Display name is required'),
  api_key: z.string().min(1, 'API key is required'),
  api_secret: z.string().optional(),
  is_active: z.boolean(),
})
type SettingsValues = z.infer<typeof settingsSchema>

// ── Sync button ───────────────────────────────────────────────────────────────

function SyncButton({ channelId }: { channelId: string }) {
  const [syncing, setSyncing] = useState(false)

  async function handleSync() {
    setSyncing(true)
    try {
      await channelsService.triggerSync(channelId, 'full_sync')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <Button variant="outline" size="sm" className="gap-2" onClick={handleSync} disabled={syncing}>
      <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
      {syncing ? 'Syncing…' : 'Sync Now'}
    </Button>
  )
}

// ── Overview tab ──────────────────────────────────────────────────────────────

function OverviewTab({ channelId }: { channelId: string }) {
  const { data: channel, isLoading } = useQuery({
    queryKey: QUERY_KEYS.CHANNELS.DETAIL(channelId),
    queryFn: () => channelsService.get(channelId),
  })

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-28 rounded-xl" />
        ))}
      </div>
    )
  }

  if (!channel) return null

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>OTA Platform</CardDescription>
          <CardTitle className="text-lg">{OTA_CHANNEL_LABELS[channel.ota] ?? channel.ota}</CardTitle>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Status</CardDescription>
          <div className="mt-1">
            <ChannelHealthBadge status={channel.sync_status} />
          </div>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Last Synced</CardDescription>
          <CardTitle className="text-lg">
            {channel.last_synced_at
              ? formatRelativeTime(channel.last_synced_at)
              : 'Never'}
          </CardTitle>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Active Mappings</CardDescription>
          <CardTitle className="text-lg">{channel.mapping_count ?? '—'}</CardTitle>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Hotel ID</CardDescription>
          <CardTitle className="text-base font-mono">{channel.hotel_id}</CardTitle>
        </CardHeader>
      </Card>
      <Card>
        <CardHeader className="pb-2">
          <CardDescription>Channel Active</CardDescription>
          <div className="mt-1 flex items-center gap-2">
            {channel.is_active ? (
              <><Wifi className="h-4 w-4 text-accent-600" /><span className="text-sm font-medium text-accent-600">Active</span></>
            ) : (
              <><WifiOff className="h-4 w-4 text-muted-foreground" /><span className="text-sm font-medium text-muted-foreground">Inactive</span></>
            )}
          </div>
        </CardHeader>
      </Card>
    </div>
  )
}

// ── Settings tab ──────────────────────────────────────────────────────────────

function SettingsTab({ channelId }: { channelId: string }) {
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: channel } = useQuery({
    queryKey: QUERY_KEYS.CHANNELS.DETAIL(channelId),
    queryFn: () => channelsService.get(channelId),
  })

  const form = useForm<SettingsValues>({
    resolver: zodResolver(settingsSchema),
    values: channel
      ? {
          display_name: channel.display_name,
          api_key: channel.api_key,
          api_secret: channel.api_secret ?? '',
          is_active: channel.is_active,
        }
      : undefined,
  })

  const updateMutation = useMutation({
    mutationFn: (values: SettingsValues) => channelsService.update(channelId, values),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.CHANNELS.DETAIL(channelId) })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => channelsService.delete(channelId),
    onSuccess() {
      navigate(ROUTES.CHANNELS)
    },
  })

  return (
    <div className="max-w-lg space-y-8">
      <Form {...form}>
        <form onSubmit={form.handleSubmit((v) => updateMutation.mutate(v))} className="space-y-4">
          <FormField
            control={form.control}
            name="display_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Display Name</FormLabel>
                <FormControl><Input {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="api_key"
            render={({ field }) => (
              <FormItem>
                <FormLabel>API Key</FormLabel>
                <FormControl><Input type="password" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="api_secret"
            render={({ field }) => (
              <FormItem>
                <FormLabel>API Secret <span className="text-muted-foreground">(optional)</span></FormLabel>
                <FormControl><Input type="password" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="is_active"
            render={({ field }) => (
              <FormItem className="flex items-center justify-between rounded-lg border p-4">
                <div>
                  <FormLabel>Channel Active</FormLabel>
                  <p className="text-xs text-muted-foreground">Enable or disable ARI distribution for this channel</p>
                </div>
                <FormControl>
                  <Switch checked={field.value} onCheckedChange={field.onChange} />
                </FormControl>
              </FormItem>
            )}
          />
          <Button type="submit" disabled={updateMutation.isPending}>
            {updateMutation.isPending ? 'Saving…' : 'Save Changes'}
          </Button>
        </form>
      </Form>

      <Separator />

      {/* Danger zone */}
      <div className="rounded-lg border border-destructive/40 p-4">
        <h3 className="text-sm font-semibold text-destructive">Danger Zone</h3>
        <p className="mt-1 text-xs text-muted-foreground">
          Removing this channel will delete all mappings and sync history.
          This action cannot be undone.
        </p>
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button variant="destructive" size="sm" className="mt-3 gap-2">
              <Trash2 className="h-4 w-4" />
              Remove Channel
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Remove channel?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete the channel, all mappings, and sync history.
                This cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                onClick={() => deleteMutation.mutate()}
                disabled={deleteMutation.isPending}
              >
                {deleteMutation.isPending ? 'Removing…' : 'Remove'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ChannelDetailPage() {
  const navigate = useNavigate()
  const { channelId } = useParams<{ channelId: string }>()

  const { data: channel, isLoading } = useQuery({
    queryKey: QUERY_KEYS.CHANNELS.DETAIL(channelId!),
    queryFn: () => channelsService.get(channelId!),
    enabled: !!channelId,
  })

  if (isLoading) {
    return (
      <div className="p-6 space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 rounded-xl" />
      </div>
    )
  }

  if (!channel) return null

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate(ROUTES.CHANNELS)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-tight">{channel.display_name}</h1>
              <ChannelHealthBadge status={channel.sync_status} />
            </div>
            <p className="text-sm text-muted-foreground">
              {OTA_CHANNEL_LABELS[channel.ota] ?? channel.ota}
            </p>
          </div>
        </div>
        <SyncButton channelId={channel.id} />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview" className="gap-2">
            <LayoutDashboard className="h-4 w-4" /> Overview
          </TabsTrigger>
          <TabsTrigger value="mappings" className="gap-2">
            <Map className="h-4 w-4" /> Mappings
          </TabsTrigger>
          <TabsTrigger value="sync-log" className="gap-2">
            <History className="h-4 w-4" /> Sync Log
          </TabsTrigger>
          <TabsTrigger value="settings" className="gap-2">
            <Settings className="h-4 w-4" /> Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <OverviewTab channelId={channel.id} />
        </TabsContent>

        <TabsContent value="mappings" className="mt-4">
          <ChannelMappingTable channelId={channel.id} />
        </TabsContent>

        <TabsContent value="sync-log" className="mt-4">
          <SyncLogTable channelId={channel.id} />
        </TabsContent>

        <TabsContent value="settings" className="mt-4">
          <SettingsTab channelId={channel.id} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
