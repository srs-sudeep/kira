import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ChevronRight, ChevronLeft, Check } from 'lucide-react'
import { toast } from 'sonner'
import { format, addDays } from 'date-fns'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Checkbox } from '@/components/ui/checkbox'
import { Separator } from '@/components/ui/separator'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { cn } from '@/lib/utils'
import roomsService from '@/features/rooms/services/rooms-service'
import inventoryService from '../services/inventory-service'
import type { BulkUpdateRequest } from '@/types/inventory'

const DAYS_OF_WEEK = [
  { value: 0, label: 'Mon' },
  { value: 1, label: 'Tue' },
  { value: 2, label: 'Wed' },
  { value: 3, label: 'Thu' },
  { value: 4, label: 'Fri' },
  { value: 5, label: 'Sat' },
  { value: 6, label: 'Sun' },
]

const STEPS = ['Select Rooms', 'Schedule', 'Updates', 'Confirm'] as const

interface Target {
  room_type_id: string
  room_type_name: string
  rate_plan_id: string
  rate_plan_name: string
}

interface UpdateFields {
  rate: { enabled: boolean; value: string }
  available_rooms: { enabled: boolean; value: string }
  stop_sell: { enabled: boolean; value: boolean }
  close_to_arrival: { enabled: boolean; value: boolean }
  close_to_departure: { enabled: boolean; value: boolean }
  min_los: { enabled: boolean; value: string }
  max_los: { enabled: boolean; value: string }
}

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  calendarQueryKey: readonly unknown[]
}

export function BulkUpdateForm({ open, onOpenChange, calendarQueryKey }: Props) {
  const qc = useQueryClient()
  const [step, setStep] = useState(0)

  // Step 1 — targets
  const [selectedTargets, setSelectedTargets] = useState<Target[]>([])

  // Step 2 — schedule
  const today = format(new Date(), 'yyyy-MM-dd')
  const [fromDate, setFromDate] = useState(today)
  const [toDate, setToDate] = useState(format(addDays(new Date(), 6), 'yyyy-MM-dd'))
  const [daysOfWeek, setDaysOfWeek] = useState<number[]>([]) // empty = all

  // Step 3 — update fields
  const [fields, setFields] = useState<UpdateFields>({
    rate:               { enabled: false, value: '' },
    available_rooms:    { enabled: false, value: '' },
    stop_sell:          { enabled: false, value: false },
    close_to_arrival:   { enabled: false, value: false },
    close_to_departure: { enabled: false, value: false },
    min_los:            { enabled: false, value: '' },
    max_los:            { enabled: false, value: '' },
  })

  // Fetch room types + rate plans
  const { data: roomTypes = [] } = useQuery({
    queryKey: ['room-types'],
    queryFn: roomsService.listRoomTypes,
    enabled: open,
  })

  // Build flat list of room × rate plan
  const { data: allRatePlans = {} } = useQuery({
    queryKey: ['bulk-update', 'all-rate-plans'],
    queryFn: async () => {
      const result: Record<string, Awaited<ReturnType<typeof roomsService.listRatePlans>>> = {}
      await Promise.all(
        roomTypes.map(async (rt) => {
          result[rt.id] = await roomsService.listRatePlans(rt.id)
        }),
      )
      return result
    },
    enabled: open && roomTypes.length > 0,
  })

  const mutation = useMutation({
    mutationFn: (requests: BulkUpdateRequest[]) => inventoryService.bulkUpdate(requests),
    onSuccess() {
      qc.invalidateQueries({ queryKey: calendarQueryKey })
      toast.success('Bulk update applied successfully')
      handleClose()
    },
  })

  function handleClose() {
    onOpenChange(false)
    setStep(0)
    setSelectedTargets([])
  }

  function toggleTarget(target: Target) {
    setSelectedTargets((prev) => {
      const exists = prev.some(
        (t) =>
          t.room_type_id === target.room_type_id &&
          t.rate_plan_id === target.rate_plan_id,
      )
      return exists
        ? prev.filter(
            (t) =>
              !(
                t.room_type_id === target.room_type_id &&
                t.rate_plan_id === target.rate_plan_id
              ),
          )
        : [...prev, target]
    })
  }

  function isTargetSelected(roomTypeId: string, ratePlanId: string) {
    return selectedTargets.some(
      (t) => t.room_type_id === roomTypeId && t.rate_plan_id === ratePlanId,
    )
  }

  function toggleDayOfWeek(day: number) {
    setDaysOfWeek((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day],
    )
  }

  function updateField<K extends keyof UpdateFields>(
    key: K,
    patch: Partial<UpdateFields[K]>,
  ) {
    setFields((prev) => ({
      ...prev,
      [key]: { ...prev[key], ...patch },
    }))
  }

  function buildRequests(): BulkUpdateRequest[] {
    return selectedTargets.map((t) => ({
      room_type_id: t.room_type_id,
      rate_plan_id: t.rate_plan_id,
      from_date: fromDate,
      to_date: toDate,
      days_of_week: daysOfWeek.length > 0 ? daysOfWeek : undefined,
      ...(fields.rate.enabled && fields.rate.value !== ''
        ? { rate: Number(fields.rate.value) }
        : {}),
      ...(fields.available_rooms.enabled && fields.available_rooms.value !== ''
        ? { available_rooms: Number(fields.available_rooms.value) }
        : {}),
      ...(fields.stop_sell.enabled ? { stop_sell: fields.stop_sell.value } : {}),
      ...(fields.close_to_arrival.enabled
        ? { close_to_arrival: fields.close_to_arrival.value }
        : {}),
      ...(fields.close_to_departure.enabled
        ? { close_to_departure: fields.close_to_departure.value }
        : {}),
      ...(fields.min_los.enabled && fields.min_los.value !== ''
        ? { min_los: Number(fields.min_los.value) }
        : {}),
      ...(fields.max_los.enabled && fields.max_los.value !== ''
        ? { max_los: Number(fields.max_los.value) }
        : {}),
    }))
  }

  const canProceed = [
    selectedTargets.length > 0,                            // step 0
    fromDate && toDate && fromDate <= toDate,               // step 1
    Object.values(fields).some((f) => f.enabled),          // step 2
    true,                                                   // step 3 = confirm
  ]

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto flex flex-col">
        <SheetHeader>
          <SheetTitle>Bulk Update Inventory</SheetTitle>
          <SheetDescription>
            Apply rate and availability changes across multiple rooms and dates.
          </SheetDescription>
        </SheetHeader>

        {/* Step indicator */}
        <div className="flex items-center gap-2 py-4">
          {STEPS.map((label, i) => (
            <div key={label} className="flex items-center gap-2">
              <div
                className={cn(
                  'flex h-6 w-6 items-center justify-center rounded-full text-xs font-medium',
                  i < step
                    ? 'bg-brand-600 text-white'
                    : i === step
                      ? 'bg-brand-100 text-brand-700 ring-2 ring-brand-600 dark:bg-brand-900 dark:text-brand-300'
                      : 'bg-muted text-muted-foreground',
                )}
              >
                {i < step ? <Check className="h-3 w-3" /> : i + 1}
              </div>
              <span
                className={cn(
                  'text-xs',
                  i === step ? 'font-medium text-foreground' : 'text-muted-foreground',
                )}
              >
                {label}
              </span>
              {i < STEPS.length - 1 && (
                <ChevronRight className="h-3 w-3 text-muted-foreground" />
              )}
            </div>
          ))}
        </div>

        <Separator />

        {/* Step content */}
        <div className="flex-1 space-y-4 py-4">

          {/* Step 0 — Select room + rate plan */}
          {step === 0 && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Select the room types and rate plans to update.
              </p>
              {roomTypes.length === 0 && (
                <p className="text-sm text-muted-foreground">Loading rooms…</p>
              )}
              {roomTypes.map((rt) => (
                <div key={rt.id} className="rounded-md border p-3 space-y-2">
                  <p className="text-sm font-semibold text-foreground">{rt.name}</p>
                  <div className="space-y-1.5 pl-2">
                    {(allRatePlans[rt.id] ?? []).map((rp) => (
                      <label
                        key={rp.id}
                        className="flex items-center gap-2 cursor-pointer text-sm"
                      >
                        <Checkbox
                          checked={isTargetSelected(rt.id, rp.id)}
                          onCheckedChange={() =>
                            toggleTarget({
                              room_type_id: rt.id,
                              room_type_name: rt.name,
                              rate_plan_id: rp.id,
                              rate_plan_name: rp.name,
                            })
                          }
                        />
                        <span>{rp.name}</span>
                        <span className="text-xs text-muted-foreground ml-auto">
                          ₹{rp.base_rate}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Step 1 — Schedule */}
          {step === 1 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Define the date range and which days of the week to apply changes.
              </p>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <Label>From Date</Label>
                  <Input
                    type="date"
                    value={fromDate}
                    min={today}
                    onChange={(e) => setFromDate(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>To Date</Label>
                  <Input
                    type="date"
                    value={toDate}
                    min={fromDate}
                    onChange={(e) => setToDate(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Days of Week</Label>
                <p className="text-xs text-muted-foreground">
                  Leave all unchecked to apply to every day.
                </p>
                <div className="flex gap-2 flex-wrap">
                  {DAYS_OF_WEEK.map((d) => (
                    <button
                      key={d.value}
                      type="button"
                      onClick={() => toggleDayOfWeek(d.value)}
                      className={cn(
                        'rounded-md px-3 py-1.5 text-xs font-medium border transition-colors',
                        daysOfWeek.includes(d.value)
                          ? 'bg-brand-600 text-white border-brand-600'
                          : 'bg-background text-muted-foreground border-border hover:border-brand-400',
                      )}
                    >
                      {d.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2 — Update values */}
          {step === 2 && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Enable the fields you want to update. Disabled fields are left unchanged.
              </p>

              {/* Numeric fields */}
              {([
                { key: 'rate' as const, label: 'Rate (₹)', type: 'number', min: 0 },
                { key: 'available_rooms' as const, label: 'Available Rooms', type: 'number', min: 0 },
                { key: 'min_los' as const, label: 'Min Nights (LOS)', type: 'number', min: 1 },
                { key: 'max_los' as const, label: 'Max Nights (LOS)', type: 'number', min: 1 },
              ]).map(({ key, label, type, min }) => (
                <div key={key} className="flex items-center gap-3 rounded-md border p-3">
                  <Checkbox
                    checked={fields[key].enabled}
                    onCheckedChange={(c) => updateField(key, { enabled: !!c })}
                  />
                  <Label className="flex-1 text-sm">{label}</Label>
                  <Input
                    type={type}
                    min={min}
                    value={(fields[key] as { enabled: boolean; value: string }).value}
                    disabled={!fields[key].enabled}
                    onChange={(e) => updateField(key, { value: e.target.value } as Partial<typeof fields[typeof key]>)}
                    className="w-28 disabled:opacity-40"
                  />
                </div>
              ))}

              {/* Boolean toggles */}
              {([
                { key: 'stop_sell' as const, label: 'Stop Sell' },
                { key: 'close_to_arrival' as const, label: 'Close to Arrival' },
                { key: 'close_to_departure' as const, label: 'Close to Departure' },
              ]).map(({ key, label }) => (
                <div key={key} className="flex items-center gap-3 rounded-md border p-3">
                  <Checkbox
                    checked={fields[key].enabled}
                    onCheckedChange={(c) => updateField(key, { enabled: !!c })}
                  />
                  <Label className="flex-1 text-sm">{label}</Label>
                  <Switch
                    checked={(fields[key] as { enabled: boolean; value: boolean }).value}
                    disabled={!fields[key].enabled}
                    onCheckedChange={(c) =>
                      updateField(key, { value: c } as Partial<typeof fields[typeof key]>)
                    }
                    className="disabled:opacity-40"
                  />
                </div>
              ))}
            </div>
          )}

          {/* Step 3 — Confirm */}
          {step === 3 && (
            <div className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Review the update before applying.
              </p>

              <div className="rounded-md border bg-muted/30 p-4 space-y-3 text-sm">
                <div>
                  <p className="font-medium text-foreground mb-1">Targets ({selectedTargets.length})</p>
                  {selectedTargets.map((t) => (
                    <p key={`${t.room_type_id}-${t.rate_plan_id}`} className="text-muted-foreground text-xs">
                      {t.room_type_name} · {t.rate_plan_name}
                    </p>
                  ))}
                </div>

                <Separator />

                <div>
                  <p className="font-medium text-foreground mb-1">Date Range</p>
                  <p className="text-muted-foreground text-xs">
                    {fromDate} → {toDate}
                    {daysOfWeek.length > 0 &&
                      ` · ${daysOfWeek.map((d) => DAYS_OF_WEEK[d].label).join(', ')} only`}
                  </p>
                </div>

                <Separator />

                <div>
                  <p className="font-medium text-foreground mb-1">Changes</p>
                  {Object.entries(fields)
                    .filter(([, f]) => f.enabled)
                    .map(([key, f]) => (
                      <p key={key} className="text-muted-foreground text-xs capitalize">
                        {key.replace(/_/g, ' ')}: <span className="font-medium text-foreground">{String(f.value)}</span>
                      </p>
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer navigation */}
        <Separator />
        <div className="flex items-center justify-between pt-4">
          <Button
            variant="ghost"
            onClick={() => (step === 0 ? handleClose() : setStep((s) => s - 1))}
            disabled={mutation.isPending}
          >
            {step === 0 ? 'Cancel' : (
              <>
                <ChevronLeft className="mr-1 h-4 w-4" /> Back
              </>
            )}
          </Button>

          {step < STEPS.length - 1 ? (
            <Button
              onClick={() => setStep((s) => s + 1)}
              disabled={!canProceed[step]}
            >
              Next <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          ) : (
            <Button
              onClick={() => mutation.mutate(buildRequests())}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? 'Applying…' : 'Apply Update'}
            </Button>
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
