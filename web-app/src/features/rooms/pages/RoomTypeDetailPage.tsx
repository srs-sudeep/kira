import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Pencil, ArrowLeft, BedDouble, Users, CheckCircle2, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { PageHeader } from '@/components/shared/PageHeader'
import { LoadingState } from '@/components/shared/LoadingState'
import { ErrorState } from '@/components/shared/ErrorState'
import { RoomTypeForm } from '../components/RoomTypeForm'
import { RatePlanTable } from '../components/RatePlanTable'
import { ROUTES } from '@/router/routes'
import roomsService from '../services/rooms-service'

export default function RoomTypeDetailPage() {
  const { roomId } = useParams<{ roomId: string }>()
  const navigate = useNavigate()
  const [editOpen, setEditOpen] = useState(false)

  const {
    data: room,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['room-types', roomId],
    queryFn: () => roomsService.getRoomType(roomId!),
    enabled: !!roomId,
  })

  if (isLoading) return <LoadingState message="Loading room type…" />
  if (isError || !room)
    return <ErrorState message="Room type not found." onRetry={refetch} />

  return (
    <>
      <PageHeader
        title={room.name}
        description={`Code: ${room.code}`}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(ROUTES.ROOMS)}
            >
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
              Back
            </Button>
            <Button size="sm" onClick={() => setEditOpen(true)}>
              <Pencil className="mr-1.5 h-3.5 w-3.5" />
              Edit
            </Button>
          </div>
        }
      />

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="rate-plans">Rate Plans</TabsTrigger>
        </TabsList>

        {/* ── Overview ─────────────────────────────────────────────────────── */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Room details card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground">Name</p>
                    <p className="font-medium text-foreground">{room.name}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Code</p>
                    <p className="font-mono font-medium text-foreground">{room.code}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <BedDouble className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Total Rooms</p>
                      <p className="font-medium text-foreground">{room.total_rooms}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Occupancy</p>
                      <p className="font-medium text-foreground">
                        {room.base_occupancy} – {room.max_occupancy} guests
                      </p>
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="flex items-center gap-2">
                  {room.is_active ? (
                    <CheckCircle2 className="h-4 w-4 text-accent-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-muted-foreground" />
                  )}
                  <span className="text-sm text-foreground">
                    {room.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                {room.description && (
                  <p className="text-sm text-muted-foreground">{room.description}</p>
                )}
              </CardContent>
            </Card>

            {/* Amenities card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Amenities ({room.amenities.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                {room.amenities.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No amenities listed.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {room.amenities.map((a) => (
                      <Badge key={a} variant="secondary">
                        {a}
                      </Badge>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* ── Rate Plans ───────────────────────────────────────────────────── */}
        <TabsContent value="rate-plans">
          <RatePlanTable roomTypeId={room.id} />
        </TabsContent>
      </Tabs>

      <RoomTypeForm open={editOpen} onOpenChange={setEditOpen} roomType={room} />
    </>
  )
}
