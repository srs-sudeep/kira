import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format, addDays, eachDayOfInterval, parseISO } from 'date-fns'
import { Settings2, Sliders, Ban } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { PageHeader } from '@/components/shared/PageHeader'
import { AriCalendarGrid } from '../components/AriCalendarGrid'
import { BulkUpdateForm } from '../components/BulkUpdateForm'
import { StopSellDialog } from '../components/StopSellDialog'
import { BlackoutDateManager } from '../components/BlackoutDateManager'
import roomsService from '@/features/rooms/services/rooms-service'
import inventoryService from '../services/inventory-service'

const TODAY = format(new Date(), 'yyyy-MM-dd')
const DEFAULT_END = format(addDays(new Date(), 29), 'yyyy-MM-dd')

export default function CalendarPage() {
  const [fromDate, setFromDate] = useState(TODAY)
  const [toDate, setToDate] = useState(DEFAULT_END)
  const [filterRoomTypeId, setFilterRoomTypeId] = useState<string>('_all')
  const [bulkOpen, setBulkOpen] = useState(false)
  const [stopSellOpen, setStopSellOpen] = useState(false)
  const [blackoutOpen, setBlackoutOpen] = useState(false)

  const queryKey = [
    'inventory',
    'calendar',
    fromDate,
    toDate,
    filterRoomTypeId,
  ] as const

  const { data: roomTypes = [] } = useQuery({
    queryKey: ['room-types'],
    queryFn: roomsService.listRoomTypes,
  })

  const { data: rows = [], isLoading } = useQuery({
    queryKey,
    queryFn: () =>
      inventoryService.getCalendar(
        fromDate,
        toDate,
        filterRoomTypeId === '_all' ? undefined : filterRoomTypeId,
      ),
    enabled: !!fromDate && !!toDate && fromDate <= toDate,
  })

  // Generate ordered date array for columns
  const dates = useMemo(() => {
    if (!fromDate || !toDate || fromDate > toDate) return []
    return eachDayOfInterval({
      start: parseISO(fromDate),
      end: parseISO(toDate),
    }).map((d) => format(d, 'yyyy-MM-dd'))
  }, [fromDate, toDate])

  return (
    <>
      <PageHeader
        title="Inventory Calendar"
        description="Manage rates and availability across room types and rate plans."
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setBlackoutOpen((p) => !p)}
            >
              <Ban className="mr-1.5 h-3.5 w-3.5" />
              Blackouts
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setStopSellOpen(true)}
            >
              <Sliders className="mr-1.5 h-3.5 w-3.5" />
              Stop Sell
            </Button>
            <Button size="sm" onClick={() => setBulkOpen(true)}>
              <Settings2 className="mr-1.5 h-3.5 w-3.5" />
              Bulk Update
            </Button>
          </div>
        }
      />

      {/* Filters bar */}
      <div className="mb-4 flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <Label className="text-xs">From</Label>
          <Input
            type="date"
            value={fromDate}
            onChange={(e) => setFromDate(e.target.value)}
            className="h-9 w-36"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">To</Label>
          <Input
            type="date"
            value={toDate}
            min={fromDate}
            onChange={(e) => setToDate(e.target.value)}
            className="h-9 w-36"
          />
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs">Room Type</Label>
          <Select value={filterRoomTypeId} onValueChange={setFilterRoomTypeId}>
            <SelectTrigger className="h-9 w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="_all">All room types</SelectItem>
              {roomTypes.map((rt) => (
                <SelectItem key={rt.id} value={rt.id}>
                  {rt.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <p className="ml-auto text-xs text-muted-foreground self-end pb-2">
          {dates.length} days · {rows.length} room/rate combinations
        </p>
      </div>

      {/* Blackout manager (inline toggle) */}
      {blackoutOpen && (
        <div className="mb-4">
          <BlackoutDateManager />
        </div>
      )}

      {/* Calendar grid */}
      <AriCalendarGrid rows={rows} dates={dates} queryKey={queryKey} isLoading={isLoading} />

      {/* Bulk update sheet */}
      <BulkUpdateForm
        open={bulkOpen}
        onOpenChange={setBulkOpen}
        calendarQueryKey={queryKey}
      />

      {/* Stop sell dialog */}
      <StopSellDialog
        open={stopSellOpen}
        onOpenChange={setStopSellOpen}
        calendarQueryKey={queryKey}
      />
    </>
  )
}
