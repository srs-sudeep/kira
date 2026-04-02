import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, addDays } from 'date-fns'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import roomsService from '@/features/rooms/services/rooms-service'
import inventoryService from '../services/inventory-service'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  calendarQueryKey: readonly unknown[]
  preselect?: { roomTypeId: string; ratePlanId: string }
}

export function StopSellDialog({ open, onOpenChange, calendarQueryKey, preselect }: Props) {
  const qc = useQueryClient()
  const today = format(new Date(), 'yyyy-MM-dd')

  const [roomTypeId, setRoomTypeId] = useState(preselect?.roomTypeId ?? '')
  const [ratePlanId, setRatePlanId] = useState(preselect?.ratePlanId ?? '')
  const [fromDate, setFromDate] = useState(today)
  const [toDate, setToDate] = useState(format(addDays(new Date(), 6), 'yyyy-MM-dd'))
  const [stopSell, setStopSell] = useState(true)

  const { data: roomTypes = [] } = useQuery({
    queryKey: ['room-types'],
    queryFn: roomsService.listRoomTypes,
    enabled: open,
  })

  const { data: ratePlans = [] } = useQuery({
    queryKey: ['room-types', roomTypeId, 'rate-plans'],
    queryFn: () => roomsService.listRatePlans(roomTypeId),
    enabled: !!roomTypeId,
  })

  const mutation = useMutation({
    mutationFn: () =>
      inventoryService.bulkUpdate([
        {
          room_type_id: roomTypeId,
          rate_plan_id: ratePlanId,
          from_date: fromDate,
          to_date: toDate,
          stop_sell: stopSell,
        },
      ]),
    onSuccess() {
      qc.invalidateQueries({ queryKey: calendarQueryKey })
      toast.success(`Stop sell ${stopSell ? 'enabled' : 'disabled'} for selected dates`)
      onOpenChange(false)
    },
  })

  const canSubmit = roomTypeId && ratePlanId && fromDate && toDate && fromDate <= toDate

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Stop Sell</DialogTitle>
          <DialogDescription>
            Quickly enable or disable stop sell for a room type, rate plan, and date range.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Room Type */}
          <div className="space-y-1.5">
            <Label>Room Type</Label>
            <Select
              value={roomTypeId}
              onValueChange={(v) => {
                setRoomTypeId(v)
                setRatePlanId('')
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select room type…" />
              </SelectTrigger>
              <SelectContent>
                {roomTypes.map((rt) => (
                  <SelectItem key={rt.id} value={rt.id}>
                    {rt.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Rate Plan */}
          <div className="space-y-1.5">
            <Label>Rate Plan</Label>
            <Select
              value={ratePlanId}
              onValueChange={setRatePlanId}
              disabled={!roomTypeId}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select rate plan…" />
              </SelectTrigger>
              <SelectContent>
                {ratePlans.map((rp) => (
                  <SelectItem key={rp.id} value={rp.id}>
                    {rp.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Date range */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>From</Label>
              <Input
                type="date"
                value={fromDate}
                min={today}
                onChange={(e) => setFromDate(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label>To</Label>
              <Input
                type="date"
                value={toDate}
                min={fromDate}
                onChange={(e) => setToDate(e.target.value)}
              />
            </div>
          </div>

          {/* Toggle */}
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <p className="text-sm font-medium">Stop Sell</p>
              <p className="text-xs text-muted-foreground">
                {stopSell ? 'Will be enabled for this period' : 'Will be disabled for this period'}
              </p>
            </div>
            <Switch checked={stopSell} onCheckedChange={setStopSell} />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate()}
            disabled={!canSubmit || mutation.isPending}
            variant={stopSell ? 'destructive' : 'default'}
          >
            {mutation.isPending
              ? 'Saving…'
              : stopSell
                ? 'Enable Stop Sell'
                : 'Disable Stop Sell'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
