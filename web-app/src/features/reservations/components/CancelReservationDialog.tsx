import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import reservationsService from '../services/reservations-service'

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  reservationId: string
  bookingReference: string
  onSuccess?: () => void
}

export function CancelReservationDialog({
  open,
  onOpenChange,
  reservationId,
  bookingReference,
  onSuccess,
}: Props) {
  const qc = useQueryClient()
  const [reason, setReason] = useState('')

  const mutation = useMutation({
    mutationFn: () => reservationsService.cancel(reservationId, reason.trim()),
    onSuccess() {
      qc.invalidateQueries({ queryKey: ['reservations'] })
      qc.invalidateQueries({ queryKey: ['reservations', reservationId] })
      toast.success(`Reservation ${bookingReference} cancelled`)
      setReason('')
      onOpenChange(false)
      onSuccess?.()
    },
  })

  function handleClose() {
    setReason('')
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-destructive/10">
              <AlertTriangle className="h-5 w-5 text-destructive" />
            </div>
            <div>
              <DialogTitle>Cancel Reservation</DialogTitle>
              <DialogDescription className="mt-0.5">
                {bookingReference}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-3 py-2">
          <p className="text-sm text-muted-foreground">
            This will cancel the reservation and notify the guest. This action cannot be undone.
          </p>

          <div className="space-y-1.5">
            <Label htmlFor="cancel-reason">Cancellation Reason</Label>
            <Textarea
              id="cancel-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Provide a reason for cancellation…"
              rows={3}
              className="resize-none"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={mutation.isPending}>
            Keep Reservation
          </Button>
          <Button
            variant="destructive"
            onClick={() => mutation.mutate()}
            disabled={!reason.trim() || mutation.isPending}
          >
            {mutation.isPending ? 'Cancelling…' : 'Cancel Reservation'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
