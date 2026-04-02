import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2, Send, MessageSquare } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { EmptyState } from '@/components/shared/EmptyState'
import { formatRelativeTime, getInitials } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import reservationsService, { type ReservationNote } from '../services/reservations-service'

interface Props {
  reservationId: string
}

const queryKey = (id: string) => ['reservations', id, 'notes']

export function ReservationNotes({ reservationId }: Props) {
  const qc = useQueryClient()
  const currentUser = useAuthStore((s) => s.user)
  const [body, setBody] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<ReservationNote | undefined>()
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { data: notes = [], isLoading } = useQuery({
    queryKey: queryKey(reservationId),
    queryFn: () => reservationsService.listNotes(reservationId),
  })

  const addMutation = useMutation({
    mutationFn: () => reservationsService.addNote(reservationId, body.trim()),
    onSuccess() {
      qc.invalidateQueries({ queryKey: queryKey(reservationId) })
      setBody('')
      textareaRef.current?.focus()
    },
    onError() {
      toast.error('Failed to add note')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (noteId: string) =>
      reservationsService.deleteNote(reservationId, noteId),
    onSuccess() {
      qc.invalidateQueries({ queryKey: queryKey(reservationId) })
      setDeleteTarget(undefined)
    },
    onError() {
      toast.error('Failed to delete note')
    },
  })

  function handleSubmit() {
    if (!body.trim()) return
    addMutation.mutate()
  }

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">Notes</h3>

      {/* Add note */}
      <div className="flex gap-3">
        <Avatar className="h-7 w-7 shrink-0 mt-0.5">
          <AvatarFallback className="bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300 text-xs">
            {currentUser ? getInitials(currentUser.full_name) : 'ME'}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 space-y-2">
          <Textarea
            ref={textareaRef}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Add an internal note…"
            rows={2}
            className="resize-none text-sm"
            onKeyDown={(e) => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault()
                handleSubmit()
              }
            }}
          />
          <div className="flex items-center justify-between">
            <p className="text-xs text-muted-foreground">Ctrl+Enter to submit</p>
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={!body.trim() || addMutation.isPending}
              className="gap-1.5"
            >
              <Send className="h-3.5 w-3.5" />
              {addMutation.isPending ? 'Posting…' : 'Post'}
            </Button>
          </div>
        </div>
      </div>

      {/* Notes list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="flex gap-3">
              <div className="h-7 w-7 animate-pulse rounded-full bg-muted" />
              <div className="flex-1 space-y-1.5">
                <div className="h-3 w-32 animate-pulse rounded bg-muted" />
                <div className="h-10 animate-pulse rounded bg-muted" />
              </div>
            </div>
          ))}
        </div>
      ) : notes.length === 0 ? (
        <EmptyState
          icon={MessageSquare}
          title="No notes yet"
          description="Internal notes are only visible to your team."
          className="py-8"
        />
      ) : (
        <ul className="space-y-4">
          {notes.map((note) => (
            <li key={note.id} className="flex gap-3">
              <Avatar className="h-7 w-7 shrink-0 mt-0.5">
                <AvatarFallback className="bg-muted text-muted-foreground text-xs">
                  {getInitials(note.author_name)}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-foreground">
                      {note.author_name}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(note.created_at)}
                    </span>
                  </div>
                  {(currentUser?.id === note.author_id) && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-muted-foreground hover:text-destructive"
                      onClick={() => setDeleteTarget(note)}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                </div>
                <p className="mt-1 text-sm text-foreground whitespace-pre-wrap">{note.body}</p>
              </div>
            </li>
          ))}
        </ul>
      )}

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(o) => !o && setDeleteTarget(undefined)}
        title="Delete Note"
        description="This note will be permanently deleted."
        confirmLabel="Delete"
        variant="destructive"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
      />
    </div>
  )
}
