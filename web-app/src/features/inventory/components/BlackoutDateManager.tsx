import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, CalendarOff } from 'lucide-react'
import { format } from 'date-fns'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { EmptyState } from '@/components/shared/EmptyState'
import { formatDate } from '@/lib/utils'
import inventoryService, { type BlackoutDate } from '../services/inventory-service'

const QUERY_KEY = ['inventory', 'blackouts'] as const

export function BlackoutDateManager() {
  const qc = useQueryClient()
  const [deleteTarget, setDeleteTarget] = useState<BlackoutDate | undefined>()
  const [showForm, setShowForm] = useState(false)

  const today = format(new Date(), 'yyyy-MM-dd')
  const [name, setName] = useState('')
  const [fromDate, setFromDate] = useState(today)
  const [toDate, setToDate] = useState(today)

  const { data: blackouts = [], isLoading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: inventoryService.listBlackouts,
  })

  const createMutation = useMutation({
    mutationFn: () =>
      inventoryService.createBlackout({
        name,
        from_date: fromDate,
        to_date: toDate,
        affects_all: true,
      }),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEY })
      toast.success('Blackout period created')
      setShowForm(false)
      setName('')
      setFromDate(today)
      setToDate(today)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => inventoryService.deleteBlackout(id),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEY })
      toast.success('Blackout period removed')
      setDeleteTarget(undefined)
    },
  })

  const canCreate = name.trim() && fromDate && toDate && fromDate <= toDate

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="text-base">Blackout Dates</CardTitle>
          <p className="text-xs text-muted-foreground mt-0.5">
            Periods where no new bookings are accepted across all channels.
          </p>
        </div>
        <Button size="sm" variant="outline" onClick={() => setShowForm((p) => !p)}>
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          Add Period
        </Button>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Create form */}
        {showForm && (
          <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
            <p className="text-sm font-medium">New Blackout Period</p>

            <div className="space-y-1.5">
              <Label className="text-xs">Name / Reason</Label>
              <Input
                placeholder="e.g. Annual maintenance"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">From</Label>
                <Input
                  type="date"
                  value={fromDate}
                  min={today}
                  onChange={(e) => setFromDate(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">To</Label>
                <Input
                  type="date"
                  value={toDate}
                  min={fromDate}
                  onChange={(e) => setToDate(e.target.value)}
                />
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={() => createMutation.mutate()}
                disabled={!canCreate || createMutation.isPending}
              >
                {createMutation.isPending ? 'Creating…' : 'Create'}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowForm(false)}
                disabled={createMutation.isPending}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        <Separator />

        {/* Blackout list */}
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="h-4 w-48 animate-pulse rounded bg-muted" />
                <div className="h-4 w-8 animate-pulse rounded bg-muted" />
              </div>
            ))}
          </div>
        ) : blackouts.length === 0 ? (
          <EmptyState
            icon={CalendarOff}
            title="No blackout periods"
            description="Add periods to block availability across all channels."
            className="py-8"
          />
        ) : (
          <ul className="divide-y divide-border">
            {blackouts.map((b) => (
              <li key={b.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="text-sm font-medium text-foreground">{b.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(b.from_date)} – {formatDate(b.to_date)}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 text-destructive hover:text-destructive"
                  onClick={() => setDeleteTarget(b)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </CardContent>

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(o) => !o && setDeleteTarget(undefined)}
        title="Remove Blackout Period"
        description={`Remove "${deleteTarget?.name}"? Channels will become bookable again for this period.`}
        confirmLabel="Remove"
        variant="destructive"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
      />
    </Card>
  )
}
