import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { type ColumnDef } from '@tanstack/react-table'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
import { DataTable } from '@/components/shared/DataTable'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { StatusBadge } from '@/components/shared/StatusBadge'
import channelsService from '../services/channels-service'
import roomsService from '@/features/rooms/services/rooms-service'
import type { ChannelMapping } from '@/types/channel'

const schema = z.object({
  room_type_id:  z.string().min(1, 'Required'),
  rate_plan_id:  z.string().min(1, 'Required'),
  ota_room_id:   z.string().min(1, 'Required'),
  ota_rate_id:   z.string().min(1, 'Required'),
  is_active:     z.boolean(),
})
type FormValues = z.infer<typeof schema>

interface Props { channelId: string }

export function ChannelMappingTable({ channelId }: Props) {
  const qc = useQueryClient()
  const [formOpen, setFormOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<ChannelMapping | undefined>()
  const [deleteTarget, setDeleteTarget] = useState<ChannelMapping | undefined>()

  const { data: mappings = [], isLoading } = useQuery({
    queryKey: ['channels', channelId, 'mappings'],
    queryFn: () => channelsService.listMappings(channelId),
  })

  const { data: roomTypes = [] } = useQuery({
    queryKey: ['room-types'],
    queryFn: roomsService.listRoomTypes,
  })

  // Build a lookup: room_type_id → rate plans
  const { data: ratePlanMap = {} } = useQuery({
    queryKey: ['mapping-rate-plans', roomTypes.map((r) => r.id).join(',')],
    queryFn: async () => {
      const entries = await Promise.all(
        roomTypes.map(async (rt) => [
          rt.id,
          await roomsService.listRatePlans(rt.id),
        ] as const),
      )
      return Object.fromEntries(entries)
    },
    enabled: roomTypes.length > 0,
  })

  const isEdit = !!editTarget

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      room_type_id: editTarget?.room_type_id ?? '',
      rate_plan_id: editTarget?.rate_plan_id ?? '',
      ota_room_id:  editTarget?.ota_room_id ?? '',
      ota_rate_id:  editTarget?.ota_rate_id ?? '',
      is_active:    editTarget?.is_active ?? true,
    },
  })

  const selectedRoomTypeId = form.watch('room_type_id')
  const availableRatePlans = ratePlanMap[selectedRoomTypeId] ?? []

  function openCreate() {
    setEditTarget(undefined)
    form.reset({ room_type_id: '', rate_plan_id: '', ota_room_id: '', ota_rate_id: '', is_active: true })
    setFormOpen(true)
  }

  function openEdit(m: ChannelMapping) {
    setEditTarget(m)
    form.reset({
      room_type_id: m.room_type_id,
      rate_plan_id: m.rate_plan_id,
      ota_room_id:  m.ota_room_id,
      ota_rate_id:  m.ota_rate_id,
      is_active:    m.is_active,
    })
    setFormOpen(true)
  }

  const saveMutation = useMutation({
    mutationFn: (values: FormValues) =>
      isEdit
        ? channelsService.updateMapping(channelId, editTarget!.id, values)
        : channelsService.createMapping(channelId, values),
    onSuccess() {
      qc.invalidateQueries({ queryKey: ['channels', channelId, 'mappings'] })
      toast.success(isEdit ? 'Mapping updated' : 'Mapping created')
      setFormOpen(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (m: ChannelMapping) => channelsService.deleteMapping(channelId, m.id),
    onSuccess() {
      qc.invalidateQueries({ queryKey: ['channels', channelId, 'mappings'] })
      toast.success('Mapping deleted')
      setDeleteTarget(undefined)
    },
  })

  // Build name lookups
  const roomTypeNames = Object.fromEntries(roomTypes.map((r) => [r.id, r.name]))
  const ratePlanNames = Object.fromEntries(
    Object.values(ratePlanMap)
      .flat()
      .map((rp) => [rp.id, rp.name]),
  )

  const columns: ColumnDef<ChannelMapping>[] = [
    {
      id: 'our_room',
      header: 'Room Type',
      cell: ({ row }) => (
        <div>
          <p className="text-sm font-medium text-foreground">
            {roomTypeNames[row.original.room_type_id] ?? row.original.room_type_id}
          </p>
          <p className="text-xs text-muted-foreground">
            {ratePlanNames[row.original.rate_plan_id] ?? row.original.rate_plan_id}
          </p>
        </div>
      ),
    },
    {
      accessorKey: 'ota_room_id',
      header: 'OTA Room ID',
      cell: ({ getValue }) => (
        <span className="font-mono text-xs text-foreground">{getValue<string>()}</span>
      ),
    },
    {
      accessorKey: 'ota_rate_id',
      header: 'OTA Rate ID',
      cell: ({ getValue }) => (
        <span className="font-mono text-xs text-foreground">{getValue<string>()}</span>
      ),
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ getValue }) => (
        <StatusBadge status={getValue<boolean>() ? 'active' : 'inactive'} />
      ),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(row.original)}>
            <Pencil className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-destructive hover:text-destructive"
            onClick={() => setDeleteTarget(row.original)}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      ),
    },
  ]

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            {mappings.length} mapping{mappings.length !== 1 ? 's' : ''}
          </p>
          <Button size="sm" onClick={openCreate}>
            <Plus className="mr-1.5 h-3.5 w-3.5" /> Add Mapping
          </Button>
        </div>
        <DataTable columns={columns} data={mappings} isLoading={isLoading} />
      </div>

      {/* Create / Edit Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{isEdit ? 'Edit Mapping' : 'New Mapping'}</DialogTitle>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit((v) => saveMutation.mutate(v))} className="space-y-4">
              <FormField
                control={form.control}
                name="room_type_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Room Type</FormLabel>
                    <Select value={field.value} onValueChange={(v) => { field.onChange(v); form.setValue('rate_plan_id', '') }}>
                      <FormControl><SelectTrigger><SelectValue placeholder="Select room type…" /></SelectTrigger></FormControl>
                      <SelectContent>
                        {roomTypes.map((rt) => (
                          <SelectItem key={rt.id} value={rt.id}>{rt.name}</SelectItem>
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
                    <Select value={field.value} onValueChange={field.onChange} disabled={!selectedRoomTypeId}>
                      <FormControl><SelectTrigger><SelectValue placeholder="Select rate plan…" /></SelectTrigger></FormControl>
                      <SelectContent>
                        {availableRatePlans.map((rp) => (
                          <SelectItem key={rp.id} value={rp.id}>{rp.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="grid grid-cols-2 gap-3">
                <FormField control={form.control} name="ota_room_id" render={({ field }) => (
                  <FormItem>
                    <FormLabel>OTA Room ID</FormLabel>
                    <FormControl><Input placeholder="e.g. ROOM_123" {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
                <FormField control={form.control} name="ota_rate_id" render={({ field }) => (
                  <FormItem>
                    <FormLabel>OTA Rate ID</FormLabel>
                    <FormControl><Input placeholder="e.g. RATE_456" {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )} />
              </div>
              <FormField control={form.control} name="is_active" render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <FormLabel className="text-sm">Active</FormLabel>
                  <FormControl><Switch checked={field.value} onCheckedChange={field.onChange} /></FormControl>
                </FormItem>
              )} />
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setFormOpen(false)} disabled={saveMutation.isPending}>Cancel</Button>
                <Button type="submit" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'Saving…' : isEdit ? 'Save' : 'Create'}</Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(o) => !o && setDeleteTarget(undefined)}
        title="Delete Mapping"
        description="This mapping will be removed from the channel. The OTA will no longer receive updates for this room/rate."
        confirmLabel="Delete"
        variant="destructive"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget)}
      />
    </>
  )
}
