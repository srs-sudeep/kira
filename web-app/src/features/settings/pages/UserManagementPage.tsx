import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Users } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { QUERY_KEYS } from '@/config/constants'
import usersService from '../services/users-service'
import { UserTable } from '../components/UserTable'
import { InviteUserDialog } from '../components/InviteUserDialog'
import type { InviteUserPayload } from '../services/users-service'

export default function UserManagementPage() {
  const qc = useQueryClient()
  const [inviteOpen, setInviteOpen] = useState(false)
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: [...QUERY_KEYS.USERS.LIST, search],
    queryFn: () => usersService.list({ search: search || undefined, page_size: 50 }),
  })

  const inviteMutation = useMutation({
    mutationFn: (payload: InviteUserPayload) => usersService.invite(payload),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.USERS.LIST })
      setInviteOpen(false)
    },
  })

  const users = data?.items ?? []

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Users className="h-5 w-5 text-muted-foreground" />
          <div>
            <h2 className="text-lg font-semibold">Team Members</h2>
            <p className="text-sm text-muted-foreground">
              Manage access for {data?.total ?? '—'} users
            </p>
          </div>
        </div>
        <Button size="sm" className="gap-2" onClick={() => setInviteOpen(true)}>
          <Plus className="h-4 w-4" />
          Invite User
        </Button>
      </div>

      <Input
        placeholder="Search by name or email…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="max-w-sm"
      />

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-14 w-full rounded-lg" />
          ))}
        </div>
      ) : (
        <UserTable users={users} />
      )}

      <InviteUserDialog
        open={inviteOpen}
        onOpenChange={setInviteOpen}
        onSubmit={inviteMutation.mutate}
        isSubmitting={inviteMutation.isPending}
      />
    </div>
  )
}
