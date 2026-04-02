import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { X, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
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
  FormDescription,
} from '@/components/ui/form'
import { Badge } from '@/components/ui/badge'
import type { RoomType } from '@/types/room'
import roomsService from '../services/rooms-service'

const schema = z
  .object({
    name: z.string().min(1, 'Name is required').max(100),
    code: z
      .string()
      .min(1, 'Code is required')
      .max(20)
      .regex(/^[A-Z0-9_-]+$/i, 'Alphanumeric, hyphens and underscores only'),
    description: z.string().max(500).optional(),
    max_occupancy: z.coerce.number().int().min(1).max(20),
    base_occupancy: z.coerce.number().int().min(1).max(20),
    total_rooms: z.coerce.number().int().min(1, 'At least 1 room required'),
  })
  .refine((d) => d.base_occupancy <= d.max_occupancy, {
    message: 'Cannot exceed max occupancy',
    path: ['base_occupancy'],
  })

type FormValues = z.infer<typeof schema>

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  roomType?: RoomType
}

export function RoomTypeForm({ open, onOpenChange, roomType }: Props) {
  const qc = useQueryClient()
  const isEdit = !!roomType
  const [amenities, setAmenities] = useState<string[]>(roomType?.amenities ?? [])
  const [amenityInput, setAmenityInput] = useState('')

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: roomType?.name ?? '',
      code: roomType?.code ?? '',
      description: roomType?.description ?? '',
      max_occupancy: roomType?.max_occupancy ?? 2,
      base_occupancy: roomType?.base_occupancy ?? 2,
      total_rooms: roomType?.total_rooms ?? 1,
    },
  })

  // Reset when dialog opens with a different room type
  useEffect(() => {
    if (open) {
      form.reset({
        name: roomType?.name ?? '',
        code: roomType?.code ?? '',
        description: roomType?.description ?? '',
        max_occupancy: roomType?.max_occupancy ?? 2,
        base_occupancy: roomType?.base_occupancy ?? 2,
        total_rooms: roomType?.total_rooms ?? 1,
      })
      setAmenities(roomType?.amenities ?? [])
    }
  }, [open, roomType])

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      isEdit
        ? roomsService.updateRoomType(roomType!.id, { ...values, amenities })
        : roomsService.createRoomType({ ...values, amenities }),
    onSuccess() {
      qc.invalidateQueries({ queryKey: ['room-types'] })
      toast.success(isEdit ? 'Room type updated' : 'Room type created')
      onOpenChange(false)
    },
  })

  function addAmenity() {
    const trimmed = amenityInput.trim()
    if (trimmed && !amenities.includes(trimmed)) {
      setAmenities((prev) => [...prev, trimmed])
    }
    setAmenityInput('')
  }

  function removeAmenity(amenity: string) {
    setAmenities((prev) => prev.filter((a) => a !== amenity))
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit Room Type' : 'New Room Type'}</DialogTitle>
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
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Deluxe Double Room" {...field} />
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
                        placeholder="DDR"
                        className="uppercase"
                        {...field}
                        onChange={(e) =>
                          field.onChange(e.target.value.toUpperCase())
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="total_rooms"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Total Rooms</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="base_occupancy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Base Occupancy</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} max={20} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="max_occupancy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Max Occupancy</FormLabel>
                    <FormControl>
                      <Input type="number" min={1} max={20} {...field} />
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
                    <Textarea
                      placeholder="Optional room description…"
                      rows={3}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {/* Amenities tag input */}
            <div className="space-y-2">
              <FormLabel>Amenities</FormLabel>
              <div className="flex gap-2">
                <Input
                  value={amenityInput}
                  onChange={(e) => setAmenityInput(e.target.value)}
                  placeholder="e.g. Air Conditioning"
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      addAmenity()
                    }
                  }}
                />
                <Button type="button" variant="outline" size="icon" onClick={addAmenity}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {amenities.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {amenities.map((a) => (
                    <Badge
                      key={a}
                      variant="secondary"
                      className="gap-1 pr-1"
                    >
                      {a}
                      <button
                        type="button"
                        onClick={() => removeAmenity(a)}
                        className="rounded-full p-0.5 hover:bg-destructive/20"
                      >
                        <X className="h-2.5 w-2.5" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
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
                {mutation.isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
