import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { format, differenceInDays, parseISO } from 'date-fns'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { CurrencyDisplay } from '@/components/shared/CurrencyDisplay'
import roomsService from '@/features/rooms/services/rooms-service'
import reservationsService from '../services/reservations-service'

const today = format(new Date(), 'yyyy-MM-dd')

const schema = z
  .object({
    room_type_id: z.string().min(1, 'Select a room type'),
    rate_plan_id: z.string().min(1, 'Select a rate plan'),
    check_in_date: z.string().min(1, 'Check-in date is required'),
    check_out_date: z.string().min(1, 'Check-out date is required'),
    adults: z.coerce.number().int().min(1).max(10),
    children: z.coerce.number().int().min(0).max(10),
    guest_first_name: z.string().min(1, 'First name is required'),
    guest_last_name: z.string().min(1, 'Last name is required'),
    guest_email: z.string().email('Valid email required'),
    guest_phone: z.string().optional(),
    special_requests: z.string().max(500).optional(),
  })
  .refine((d) => d.check_out_date > d.check_in_date, {
    message: 'Check-out must be after check-in',
    path: ['check_out_date'],
  })

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreateReservationDialog({ open, onOpenChange }: Props) {
  const qc = useQueryClient()

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      room_type_id: '',
      rate_plan_id: '',
      check_in_date: today,
      check_out_date: '',
      adults: 1,
      children: 0,
      guest_first_name: '',
      guest_last_name: '',
      guest_email: '',
      guest_phone: '',
      special_requests: '',
    },
  })

  const roomTypeId = form.watch('room_type_id')
  const ratePlanId = form.watch('rate_plan_id')
  const checkIn = form.watch('check_in_date')
  const checkOut = form.watch('check_out_date')

  // Clear rate plan when room type changes
  useEffect(() => {
    form.setValue('rate_plan_id', '')
  }, [roomTypeId])

  useEffect(() => {
    if (open) form.reset()
  }, [open])

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

  // Compute estimated total
  const selectedPlan = ratePlans.find((p) => p.id === ratePlanId)
  const nights =
    checkIn && checkOut && checkOut > checkIn
      ? differenceInDays(parseISO(checkOut), parseISO(checkIn))
      : 0
  const estimatedTotal = selectedPlan ? selectedPlan.base_rate * nights : 0

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      reservationsService.create({
        room_type_id: values.room_type_id,
        rate_plan_id: values.rate_plan_id,
        check_in_date: values.check_in_date,
        check_out_date: values.check_out_date,
        adults: values.adults,
        children: values.children,
        guest: {
          first_name: values.guest_first_name,
          last_name: values.guest_last_name,
          email: values.guest_email,
          phone: values.guest_phone,
        },
        special_requests: values.special_requests,
      }),
    onSuccess(data) {
      qc.invalidateQueries({ queryKey: ['reservations'] })
      toast.success(`Reservation ${data.booking_reference} created`)
      onOpenChange(false)
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>New Reservation</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((v) => mutation.mutate(v))}
            className="space-y-5"
          >
            {/* Room + Rate */}
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Room &amp; Rate
              </p>
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="room_type_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Room Type</FormLabel>
                      <Select value={field.value} onValueChange={field.onChange}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select room…" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {roomTypes.map((rt) => (
                            <SelectItem key={rt.id} value={rt.id}>
                              {rt.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="rate_plan_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Rate Plan</FormLabel>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                        disabled={!roomTypeId}
                      >
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select rate…" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {ratePlans.map((rp) => (
                            <SelectItem key={rp.id} value={rp.id}>
                              {rp.name} — ₹{rp.base_rate}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </div>

            <Separator />

            {/* Dates + Occupancy */}
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Stay
              </p>
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="check_in_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Check-in</FormLabel>
                      <FormControl>
                        <Input type="date" min={today} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="check_out_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Check-out</FormLabel>
                      <FormControl>
                        <Input type="date" min={checkIn || today} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="adults"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Adults</FormLabel>
                      <FormControl>
                        <Input type="number" min={1} max={10} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="children"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Children</FormLabel>
                      <FormControl>
                        <Input type="number" min={0} max={10} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              {/* Estimated total */}
              {nights > 0 && selectedPlan && (
                <div className="flex items-center justify-between rounded-md bg-muted/40 px-3 py-2 text-sm">
                  <span className="text-muted-foreground">
                    {nights} night{nights !== 1 ? 's' : ''} × ₹{selectedPlan.base_rate}
                  </span>
                  <CurrencyDisplay amount={estimatedTotal} size="sm" className="font-semibold" />
                </div>
              )}
            </div>

            <Separator />

            {/* Guest info */}
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Guest
              </p>
              <div className="grid grid-cols-2 gap-3">
                <FormField
                  control={form.control}
                  name="guest_first_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>First Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Jane" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="guest_last_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Last Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Doe" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="guest_email"
                  render={({ field }) => (
                    <FormItem className="col-span-2">
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input type="email" placeholder="jane@example.com" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="guest_phone"
                  render={({ field }) => (
                    <FormItem className="col-span-2">
                      <FormLabel>Phone (optional)</FormLabel>
                      <FormControl>
                        <Input type="tel" placeholder="+91 98765 43210" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="special_requests"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Special Requests (optional)</FormLabel>
                    <FormControl>
                      <Textarea rows={2} placeholder="e.g. High floor, late check-in" className="resize-none" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={mutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? 'Creating…' : 'Create Reservation'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
