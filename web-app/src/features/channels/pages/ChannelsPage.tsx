import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Radio } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet'
import { useAuthStore } from '@/stores/auth-store'
import { QUERY_KEYS } from '@/config/constants'
import channelsService from '../services/channels-service'
import { ChannelCard } from '../components/ChannelCard'
import { ConnectChannelWizard } from '../components/ConnectChannelWizard'

export default function ChannelsPage() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const [connectOpen, setConnectOpen] = useState(false)

  const { data: channels = [], isLoading } = useQuery({
    queryKey: QUERY_KEYS.CHANNELS.LIST(user?.tenant_id ?? ''),
    queryFn: channelsService.list,
    enabled: !!user?.tenant_id,
  })

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Channels</h1>
          <p className="text-sm text-muted-foreground">
            Manage your OTA connections and distribution
          </p>
        </div>
        <Button className="gap-2" onClick={() => setConnectOpen(true)}>
          <Plus className="h-4 w-4" />
          Connect Channel
        </Button>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-52 rounded-xl" />
          ))}
        </div>
      ) : channels.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed py-20 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
            <Radio className="h-6 w-6 text-muted-foreground" />
          </div>
          <div>
            <p className="font-semibold">No channels connected</p>
            <p className="text-sm text-muted-foreground">
              Connect your first OTA to start distributing your inventory
            </p>
          </div>
          <Button className="gap-2" onClick={() => setConnectOpen(true)}>
            <Plus className="h-4 w-4" />
            Connect Channel
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {channels.map((channel) => (
            <ChannelCard
              key={channel.id}
              channel={channel}
            />
          ))}
        </div>
      )}

      {/* Connect wizard sheet */}
      <Sheet open={connectOpen} onOpenChange={setConnectOpen}>
        <SheetContent side="right" className="w-full sm:max-w-lg overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Connect a Channel</SheetTitle>
          </SheetHeader>
          <div className="mt-6">
            <ConnectChannelWizard />
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
