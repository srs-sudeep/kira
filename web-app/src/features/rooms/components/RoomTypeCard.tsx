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
      className={cn(
        'group cursor-pointer overflow-hidden border-border/40 bg-card/75 glass shadow-lg hover-lift',
      )}
      onClick={onClick}
    >
      {/* Gradient top accent */}
      <div className="h-1 w-full bg-gradient-to-r from-primary/50 via-accent-500/60 to-primary/50 opacity-90 dark:from-primary/40 dark:via-accent-500/50 dark:to-primary/40" />
      <div className="relative h-36 overflow-hidden bg-gradient-to-br from-primary/[0.08] via-primary/[0.04] to-accent-500/[0.12] dark:from-primary/15 dark:via-primary/10 dark:to-accent-500/20">
        <div className="absolute inset-0 flex items-center justify-center">
          <BedDouble className="h-12 w-12 text-primary/25 dark:text-primary/30" />
        </div>
        <div className="absolute right-2.5 top-2.5">
          <Badge
            variant={roomType.is_active ? 'default' : 'secondary'}
            className={cn(
              'border-0 text-[11px] font-medium shadow-none backdrop-blur-sm',
              roomType.is_active
                ? 'bg-primary/20 text-primary hover:bg-primary/25 dark:bg-primary/25'
                : 'bg-muted/50 text-muted-foreground',
            )}
          >
            {roomType.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
        <div
          className="absolute left-2.5 top-2.5 opacity-0 transition-opacity group-hover:opacity-100"
          onClick={(e) => e.stopPropagation()}
        >
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="secondary" size="icon" className="h-7 w-7 border-border/30 bg-background/70 glass">
                <MoreHorizontal className="h-3.5 w-3.5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem onClick={onEdit} className="gap-2">
                <Pencil className="h-3.5 w-3.5" /> Edit
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={onDelete} className="gap-2 text-destructive focus:text-destructive">
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
            <p className="flex items-center gap-1 text-xs text-muted-foreground/70">
              <Hash className="h-3 w-3" />
              {roomType.code}
            </p>
          </div>
        </div>
        {roomType.description && (
          <p className="mt-2 line-clamp-2 text-xs text-muted-foreground/75">{roomType.description}</p>
        )}
        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground/85">
          <span className="flex items-center gap-1">
            <Users className="h-3.5 w-3.5" />
            Max {roomType.max_occupancy}
          </span>
          <span className="flex items-center gap-1">
            <BedDouble className="h-3.5 w-3.5" />
            {roomType.total_rooms} rooms
          </span>
        </div>
      </CardContent>
      {roomType.amenities.length > 0 && (
        <CardFooter className="flex-wrap gap-1.5 px-4 pb-4 pt-0">
          {roomType.amenities.slice(0, 4).map((a) => (
            <Badge
              key={a}
              variant="outline"
              className="border-border/35 bg-muted/15 font-normal text-[11px] text-muted-foreground backdrop-blur-sm"
            >
              {a}
            </Badge>
          ))}
          {roomType.amenities.length > 4 && (
            <Badge
              variant="outline"
              className="border-border/35 bg-muted/10 font-normal text-[11px] text-muted-foreground/80"
            >
              +{roomType.amenities.length - 4}
            </Badge>
          )}
        </CardFooter>
      )}
    </Card>
  )
}
