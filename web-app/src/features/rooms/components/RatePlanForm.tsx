import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
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
import type { RatePlan, MealPlan, CancellationPolicy } from '@/types/room'
import roomsService from '../services/rooms-service'

const MEAL_PLAN_OPTIONS: { value: MealPlan; label: string }[] = [
  { value: 'room_only', label: 'Room Only' },
  { value: 'breakfast', label: 'Breakfast Included' },
  { value: 'half_board', label: 'Half Board' },
  { value: 'full_board', label: 'Full Board' },
  { value: 'all_inclusive', label: 'All Inclusive' },
]

const CANCEL_POLICY_OPTIONS: { value: CancellationPolicy; label: string }[] = [
  { value: 'free_cancellation', label: 'Free Cancellation' },
  { value: 'non_refundable', label: 'Non-Refundable' },
  { value: 'partial_refund', label: 'Partial Refund' },
]

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  code: z
    .string()
    .min(1, 'Code is required')
    .max(20)
    .regex(/^[A-Z0-9_-]+$/i, 'Alphanumeric, hyphens and underscores only'),
  description: z.string().max(500).optional(),
  meal_plan: z.enum([
    'room_only', 'breakfast', 'half_board', 'full_board', 'all_inclusive',
  ]),
  cancellation_policy: z.enum([
    'free_cancellation', 'non_refundable', 'partial_refund',
  ]),
  base_rate: z.coerce.number().min(0, 'Rate must be ≥ 0'),
  min_los: z.coerce.number().int().min(1).optional().or(z.literal('')),
  max_los: z.coerce.number().int().min(1).optional().or(z.literal('')),
  is_refundable: z.boolean(),
})

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  roomTypeId: string
  ratePlan?: RatePlan
}

export function RatePlanForm({ open, onOpenChange, roomTypeId, ratePlan }: Props) {
  const qc = useQueryClient()
  const isEdit = !!ratePlan

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: ratePlan?.name ?? '',
      code: ratePlan?.code ?? '',
      description: ratePlan?.description ?? '',
      meal_plan: ratePlan?.meal_plan ?? 'room_only',
      cancellation_policy: ratePlan?.cancellation_policy ?? 'free_cancellation',
      base_rate: ratePlan?.base_rate ?? 0,
      min_los: ratePlan?.min_los ?? '',
      max_los: ratePlan?.max_los ?? '',
      is_refundable: ratePlan?.is_refundable ?? true,
    },
  })

  useEffect(() => {
    if (open) {
      form.reset({
        name: ratePlan?.name ?? '',
        code: ratePlan?.code ?? '',
        description: ratePlan?.description ?? '',
        meal_plan: ratePlan?.meal_plan ?? 'room_only',
        cancellation_policy: ratePlan?.cancellation_policy ?? 'free_cancellation',
        base_rate: ratePlan?.base_rate ?? 0,
        min_los: ratePlan?.min_los ?? '',
        max_los: ratePlan?.max_los ?? '',
        is_refundable: ratePlan?.is_refundable ?? true,
      })
    }
  }, [open, ratePlan])

  const mutation = useMutation({
    mutationFn: (values: FormValues) => {
      const payload = {
        ...values,
        min_los: values.min_los === '' ? undefined : Number(values.min_los),
        max_los: values.max_los === '' ? undefined : Number(values.max_los),
      }
      return isEdit
        ? roomsService.updateRatePlan(roomTypeId, ratePlan!.id, payload)
        : roomsService.createRatePlan(roomTypeId, payload as Parameters<typeof roomsService.createRatePlan>[1])
    },
    onSuccess() {
      qc.invalidateQueries({ queryKey: ['room-types', roomTypeId, 'rate-plans'] })
      toast.success(isEdit ? 'Rate plan updated' : 'Rate plan created')
      onOpenChange(false)
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit Rate Plan' : 'New Rate Plan'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form
            onSubmit={form.handleSubmit((v) => mutation.mutate(v))}
            className="space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="name"
                render={({ field }) => (
                  <FormItem className="col-span-2">
                    <FormLabel>Plan Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Standard Rate" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Code</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="STD"
                        className="uppercase"
                        {...field}
                        onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="base_rate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Base Rate (₹)</FormLabel>
                    <FormControl>
                      <Input type="number" min={0} step={0.01} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="meal_plan"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Meal Plan</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {MEAL_PLAN_OPTIONS.map((o) => (
                          <SelectItem key={o.value} value={o.value}>
                            {o.label}
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
                name="cancellation_policy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Cancellation Policy</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {CANCEL_POLICY_OPTIONS.map((o) => (
                          <SelectItem key={o.value} value={o.value}>
                            {o.label}
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
                name="min_los"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Min Nights</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} placeholder="—" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="max_los"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max Nights</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} placeholder="—" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Textarea rows={2} placeholder="Optional…" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="is_refundable"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div>
                    <FormLabel className="text-sm font-medium">Refundable</FormLabel>
                    <p className="text-xs text-muted-foreground">
                      Can the guest receive a full refund?
                    </p>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

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
                {mutation.isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
