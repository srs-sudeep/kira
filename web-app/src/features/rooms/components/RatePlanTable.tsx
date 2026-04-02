import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { type ColumnDef } from '@tanstack/react-table'
import { Pencil, Trash2, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/shared/DataTable'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { CurrencyDisplay } from '@/components/shared/CurrencyDisplay'
import { RatePlanForm } from './RatePlanForm'
import type { RatePlan } from '@/types/room'
import roomsService from '../services/rooms-service'

const MEAL_PLAN_LABELS: Record<string, string> = {
  room_only: 'Room Only',
  breakfast: 'Breakfast',
  half_board: 'Half Board',
  full_board: 'Full Board',
  all_inclusive: 'All Inclusive',
}

const CANCEL_LABELS: Record<string, string> = {
  free_cancellation: 'Free Cancel',
  non_refundable: 'Non-Refundable',
  partial_refund: 'Partial Refund',
}

interface Props {
  roomTypeId: string
}

export function RatePlanTable({ roomTypeId }: Props) {
  const qc = useQueryClient()
  const [formOpen, setFormOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<RatePlan | undefined>()
  const [deleteTarget, setDeleteTarget] = useState<RatePlan | undefined>()

  const { data = [], isLoading } = useQuery({
    queryKey: ['room-types', roomTypeId, 'rate-plans'],
    queryFn: () => roomsService.listRatePlans(roomTypeId),
    enabled: !!roomTypeId,
  })

  const deleteMutation = useMutation({
    mutationFn: (plan: RatePlan) => roomsService.deleteRatePlan(roomTypeId, plan.id),
    onSuccess() {
      qc.invalidateQueries({ queryKey: ['room-types', roomTypeId, 'rate-plans'] })
      toast.success('Rate plan deleted')
      setDeleteTarget(undefined)
    },
  })

  const columns: ColumnDef<RatePlan>[] = [
    {
      accessorKey: 'name',
      header: 'Plan Name',
      cell: ({ row }) => (
        <div>
          <p className="font-medium text-foreground">{row.original.name}</p>
          <p className="text-xs text-muted-foreground font-mono">{row.original.code}</p>
        </div>
      ),
    },
    {
      accessorKey: 'meal_plan',
      header: 'Meal Plan',
      cell: ({ getValue }) => (
        <span className="text-sm">{MEAL_PLAN_LABELS[getValue<string>()] ?? getValue<string>()}</span>
      ),
    },
    {
      accessorKey: 'base_rate',
      header: 'Base Rate',
      cell: ({ getValue }) => <CurrencyDisplay amount={getValue<number>()} size="sm" />,
    },
    {
      accessorKey: 'cancellation_policy',
      header: 'Cancellation',
      cell: ({ getValue }) => (
        <span className="text-xs text-muted-foreground">
          {CANCEL_LABELS[getValue<string>()] ?? getValue<string>()}
        </span>
      ),
    },
    {
      id: 'los',
      header: 'LOS',
      cell: ({ row }) => {
        const { min_los, max_los } = row.original
        if (!min_los && !max_los) return <span className="text-muted-foreground text-xs">—</span>
        return (
          <span className="text-xs tabular-nums">
            {min_los ?? 1}–{max_los ?? '∞'} nights
          </span>
        )
      },
    },
    {
      accessorKey: 'is_refundable',
      header: 'Refundable',
      cell: ({ getValue }) => (
        <StatusBadge
          status={getValue<boolean>() ? 'active' : 'inactive'}
          label={getValue<boolean>() ? 'Yes' : 'No'}
        />
      ),
    },
    {
      accessorKey: 'is_active',
      header: 'Status',
      cell: ({ getValue }) => (
        <StatusBadge
          status={getValue<boolean>() ? 'active' : 'inactive'}
        />
      ),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => (
        <div className="flex items-center justify-end gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => {
              setEditTarget(row.original)
              setFormOpen(true)
            }}
          >
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
            {data.length} rate plan{data.length !== 1 ? 's' : ''}
          </p>
          <Button
            size="sm"
            onClick={() => {
              setEditTarget(undefined)
              setFormOpen(true)
            }}
          >
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            Add Rate Plan
          </Button>
        </div>

        <DataTable columns={columns} data={data} isLoading={isLoading} />
      </div>

      <RatePlanForm
        open={formOpen}
        onOpenChange={(o) => {
          setFormOpen(o)
          if (!o) setEditTarget(undefined)
        }}
        roomTypeId={roomTypeId}
        ratePlan={editTarget}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(o) => !o && setDeleteTarget(undefined)}
        title="Delete Rate Plan"
        description={`Delete "${deleteTarget?.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget)}
      />
    </>
  )
}
