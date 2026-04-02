import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  MoreHorizontal, UserCheck, UserX, Mail, Shield,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import { QUERY_KEYS, USER_ROLES } from '@/config/constants'
import type { UserRole } from '@/config/constants'
import { getInitials } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import usersService from '../services/users-service'
import type { User } from '@/types/auth'

const ROLE_LABELS: Record<UserRole, string> = {
  super_admin: 'Super Admin',
  hotel_admin: 'Hotel Admin',
  manager: 'Manager',
  front_desk: 'Front Desk',
}

const ROLE_BADGE_VARIANT: Record<UserRole, 'default' | 'secondary' | 'outline'> = {
  super_admin: 'default',
  hotel_admin: 'default',
  manager: 'secondary',
  front_desk: 'outline',
}

interface Props {
  users: User[]
}

export function UserTable({ users }: Props) {
  const qc = useQueryClient()
  const { user: currentUser } = useAuthStore()

  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: UserRole }) =>
      usersService.updateRole(id, role),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.USERS.LIST })
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => usersService.deactivate(id),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.USERS.LIST })
    },
  })

  const reactivateMutation = useMutation({
    mutationFn: (id: string) => usersService.reactivate(id),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.USERS.LIST })
    },
  })

  const resendMutation = useMutation({
    mutationFn: (id: string) => usersService.resendInvite(id),
  })

  if (users.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
        <Shield className="h-8 w-8 text-muted-foreground/40" />
        <p className="text-sm text-muted-foreground">No users found</p>
      </div>
    )
  }

  return (
    <div className="divide-y rounded-lg border">
      {users.map((u) => {
        const isSelf = u.id === currentUser?.id
        return (
          <div key={u.id} className="flex items-center gap-4 px-4 py-3">
            {/* Avatar + name */}
            <Avatar className="h-9 w-9 shrink-0">
              <AvatarImage src={u.avatar_url} alt={u.full_name} />
              <AvatarFallback className="text-xs">{getInitials(u.full_name)}</AvatarFallback>
            </Avatar>

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <p className="truncate text-sm font-medium">{u.full_name}</p>
                {isSelf && (
                  <Badge variant="outline" className="text-[10px]">You</Badge>
                )}
                {!u.is_active && (
                  <Badge variant="secondary" className="text-[10px]">Inactive</Badge>
                )}
              </div>
              <p className="truncate text-xs text-muted-foreground">{u.email}</p>
            </div>

            {/* Role select */}
            <Select
              value={u.role}
              onValueChange={(v) => roleMutation.mutate({ id: u.id, role: v as UserRole })}
              disabled={isSelf || u.role === USER_ROLES.SUPER_ADMIN || roleMutation.isPending}
            >
              <SelectTrigger className="h-7 w-36 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(ROLE_LABELS)
                  .filter(([v]) => v !== USER_ROLES.SUPER_ADMIN)
                  .map(([value, label]) => (
                    <SelectItem key={value} value={value} className="text-xs">{label}</SelectItem>
                  ))}
              </SelectContent>
            </Select>

            {/* Actions */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-7 w-7" disabled={isSelf}>
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  className="gap-2"
                  onClick={() => resendMutation.mutate(u.id)}
                  disabled={resendMutation.isPending}
                >
                  <Mail className="h-4 w-4" />
                  Resend invite
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                {u.is_active ? (
                  <DropdownMenuItem
                    className="gap-2 text-destructive focus:text-destructive"
                    onClick={() => deactivateMutation.mutate(u.id)}
                    disabled={deactivateMutation.isPending}
                  >
                    <UserX className="h-4 w-4" />
                    Deactivate
                  </DropdownMenuItem>
                ) : (
                  <DropdownMenuItem
                    className="gap-2"
                    onClick={() => reactivateMutation.mutate(u.id)}
                    disabled={reactivateMutation.isPending}
                  >
                    <UserCheck className="h-4 w-4" />
                    Reactivate
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        )
      })}
    </div>
  )
}
