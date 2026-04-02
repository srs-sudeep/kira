import { useCallback } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { SearchInput } from '@/components/shared/SearchInput'
import { DateRangePicker, type DateRange } from '@/components/shared/DateRangePicker'
import { OTA_CHANNEL_LABELS } from '@/config/constants'
import { format, parseISO } from 'date-fns'
import type { ReservationListParams, ReservationStatus } from '@/types/reservation'

const STATUS_OPTIONS: { value: ReservationStatus; label: string }[] = [
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'pending', label: 'Pending' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'no_show', label: 'No Show' },
  { value: 'checked_in', label: 'Checked In' },
  { value: 'checked_out', label: 'Checked Out' },
]

interface Props {
  filters: ReservationListParams
  onChange: (filters: ReservationListParams) => void
}

export function ReservationFilters({ filters, onChange }: Props) {
  const set = useCallback(
    (patch: Partial<ReservationListParams>) =>
      onChange({ ...filters, page: 1, ...patch }),
    [filters, onChange],
  )

  const dateRange: DateRange = {
    from: filters.check_in_from ? parseISO(filters.check_in_from) : undefined,
    to: filters.check_in_to ? parseISO(filters.check_in_to) : undefined,
  }

  function handleDateRange(range: DateRange) {
    set({
      check_in_from: range.from ? format(range.from, 'yyyy-MM-dd') : undefined,
      check_in_to: range.to ? format(range.to, 'yyyy-MM-dd') : undefined,
    })
  }

  // Count active filters for badge
  const activeCount = [
    filters.search,
    filters.status,
    filters.channel,
    filters.check_in_from,
  ].filter(Boolean).length

  function clearAll() {
    onChange({ page: 1, page_size: filters.page_size })
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        {/* Search */}
        <SearchInput
          value={filters.search ?? ''}
          onChange={(v) => set({ search: v || undefined })}
          placeholder="Guest, booking ref, email…"
          className="w-64"
        />

        {/* Status */}
        <Select
          value={filters.status ?? '_all'}
          onValueChange={(v) => set({ status: v === '_all' ? undefined : (v as ReservationStatus) })}
        >
          <SelectTrigger className="w-36 h-9">
            <SelectValue placeholder="All statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="_all">All statuses</SelectItem>
            {STATUS_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Channel */}
        <Select
          value={filters.channel ?? '_all'}
          onValueChange={(v) => set({ channel: v === '_all' ? undefined : v })}
        >
          <SelectTrigger className="w-40 h-9">
            <SelectValue placeholder="All channels" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="_all">All channels</SelectItem>
            {Object.entries(OTA_CHANNEL_LABELS).map(([value, label]) => (
              <SelectItem key={value} value={value}>
                {label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Date range */}
        <DateRangePicker
          value={dateRange}
          onChange={handleDateRange}
          placeholder="Check-in range"
          className="h-9 w-56"
        />

        {/* Clear */}
        {activeCount > 0 && (
          <Button variant="ghost" size="sm" onClick={clearAll} className="gap-1.5 h-9">
            <X className="h-3.5 w-3.5" />
            Clear
            <Badge variant="secondary" className="ml-1 text-xs">
              {activeCount}
            </Badge>
          </Button>
        )}
      </div>
    </div>
  )
}
