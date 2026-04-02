import { MoreHorizontal, BedDouble, Users, Hash, Pencil, Trash2 } from 'lucide-react'
import { Card, CardContent, CardFooter } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import type { RoomType } from '@/types/room'

interface RoomTypeCardProps {
  roomType: RoomType
  onEdit: () => void
  onDelete: () => void
  onClick: () => void
}

export function RoomTypeCard({ roomType, onEdit, onDelete, onClick }: RoomTypeCardProps) {
  return (
    <Card
      className="group cursor-pointer transition-shadow hover:shadow-md"
      onClick={onClick}
    >
      {/* Placeholder image / hero */}
      <div className="relative h-36 overflow-hidden rounded-t-lg bg-gradient-to-br from-brand-100 to-brand-200 dark:from-brand-900 dark:to-brand-800">
        <div className="absolute inset-0 flex items-center justify-center">
          <BedDouble className="h-12 w-12 text-brand-400 dark:text-brand-600" />
        </div>

        {/* Status badge */}
        <div className="absolute right-2 top-2">
          <Badge
            variant={roomType.is_active ? 'default' : 'secondary'}
            className="text-xs"
          >
            {roomType.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>

        {/* Actions menu */}
        <div
          className="absolute left-2 top-2 opacity-0 transition-opacity group-hover:opacity-100"
          onClick={(e) => e.stopPropagation()}
        >
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="secondary" size="icon" className="h-7 w-7">
                <MoreHorizontal className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem onClick={onEdit} className="gap-2">
                <Pencil className="h-3.5 w-3.5" /> Edit
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={onDelete}
                className="gap-2 text-destructive focus:text-destructive"
              >
                <Trash2 className="h-3.5 w-3.5" /> Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h3 className="truncate font-semibold text-foreground">{roomType.name}</h3>
            <p className="flex items-center gap-1 text-xs text-muted-foreground">
              <Hash className="h-3 w-3" />
              {roomType.code}
            </p>
          </div>
        </div>

        {roomType.description && (
          <p className="mt-2 line-clamp-2 text-xs text-muted-foreground">
            {roomType.description}
          </p>
        )}

        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Users className="h-3.5 w-3.5" />
            Max {roomType.max_occupancy} guests
          </span>
          <span className="flex items-center gap-1">
            <BedDouble className="h-3.5 w-3.5" />
            {roomType.total_rooms} rooms
          </span>
        </div>
      </CardContent>

      {roomType.amenities.length > 0 && (
        <CardFooter className="flex-wrap gap-1 px-4 pb-4 pt-0">
          {roomType.amenities.slice(0, 4).map((a) => (
            <Badge key={a} variant="outline" className="text-xs font-normal">
              {a}
            </Badge>
          ))}
          {roomType.amenities.length > 4 && (
            <Badge variant="outline" className="text-xs font-normal text-muted-foreground">
              +{roomType.amenities.length - 4}
            </Badge>
          )}
        </CardFooter>
      )}
    </Card>
  )
}
