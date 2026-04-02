import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, BedDouble } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/shared/PageHeader'
import { EmptyState } from '@/components/shared/EmptyState'
import { LoadingState } from '@/components/shared/LoadingState'
import { ErrorState } from '@/components/shared/ErrorState'
import { ConfirmDialog } from '@/components/shared/ConfirmDialog'
import { SearchInput } from '@/components/shared/SearchInput'
import { RoomTypeCard } from '../components/RoomTypeCard'
import { RoomTypeForm } from '../components/RoomTypeForm'
import { ROUTES } from '@/router/routes'
import type { RoomType } from '@/types/room'
import roomsService from '../services/rooms-service'

export default function RoomTypesPage() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<RoomType | undefined>()
  const [deleteTarget, setDeleteTarget] = useState<RoomType | undefined>()

  const { data = [], isLoading, isError, refetch } = useQuery({
    queryKey: ['room-types'],
    queryFn: roomsService.listRoomTypes,
  })

  const deleteMutation = useMutation({
    mutationFn: (rt: RoomType) => roomsService.deleteRoomType(rt.id),
    onSuccess() {
      qc.invalidateQueries({ queryKey: ['room-types'] })
      toast.success('Room type deleted')
      setDeleteTarget(undefined)
    },
  })

  const filtered = search
    ? data.filter(
        (rt) =>
          rt.name.toLowerCase().includes(search.toLowerCase()) ||
          rt.code.toLowerCase().includes(search.toLowerCase()),
      )
    : data

  if (isLoading) return <LoadingState message="Loading room types…" />
  if (isError)
    return <ErrorState message="Failed to load room types." onRetry={refetch} />

  return (
    <>
      <PageHeader
        title="Room Types"
        description="Manage your property's room categories and rate plans."
        actions={
          <Button
            onClick={() => {
              setEditTarget(undefined)
              setFormOpen(true)
            }}
          >
            <Plus className="mr-1.5 h-4 w-4" />
            Add Room Type
          </Button>
        }
      />

      {/* Search */}
      <div className="mb-5">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search room types…"
          className="w-64"
        />
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={BedDouble}
          title={search ? 'No room types match your search' : 'No room types yet'}
          description={
            search
              ? 'Try a different search term.'
              : 'Create your first room type to start managing inventory.'
          }
          action={
            !search ? (
              <Button
                onClick={() => {
                  setEditTarget(undefined)
                  setFormOpen(true)
                }}
              >
                <Plus className="mr-1.5 h-4 w-4" />
                Add Room Type
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((rt) => (
            <RoomTypeCard
              key={rt.id}
              roomType={rt}
              onClick={() =>
                navigate(ROUTES.ROOM_DETAIL.replace(':roomId', rt.id))
              }
              onEdit={() => {
                setEditTarget(rt)
                setFormOpen(true)
              }}
              onDelete={() => setDeleteTarget(rt)}
            />
          ))}
        </div>
      )}

      <RoomTypeForm
        open={formOpen}
        onOpenChange={(o) => {
          setFormOpen(o)
          if (!o) setEditTarget(undefined)
        }}
        roomType={editTarget}
      />

      <ConfirmDialog
        open={!!deleteTarget}
        onOpenChange={(o) => !o && setDeleteTarget(undefined)}
        title="Delete Room Type"
        description={`Delete "${deleteTarget?.name}"? All associated rate plans will also be removed. This cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        isLoading={deleteMutation.isPending}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget)}
      />
    </>
  )
}
