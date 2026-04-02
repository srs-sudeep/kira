import { Mail, Phone, Globe, CreditCard, BookOpen } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { getInitials } from '@/lib/utils'
import type { Guest } from '@/types/reservation'

interface Props {
  guest: Guest
  pastStays?: number
}

export function GuestProfileCard({ guest, pastStays }: Props) {
  const fullName = `${guest.first_name} ${guest.last_name}`

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">Guest</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Avatar + Name */}
        <div className="flex items-center gap-3">
          <Avatar className="h-10 w-10">
            <AvatarFallback className="bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300 text-sm font-semibold">
              {getInitials(fullName)}
            </AvatarFallback>
          </Avatar>
          <div>
            <p className="font-semibold text-foreground">{fullName}</p>
            {pastStays !== undefined && (
              <p className="text-xs text-muted-foreground">
                {pastStays} past stay{pastStays !== 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>

        {/* Contact details */}
        <ul className="space-y-2">
          <li className="flex items-center gap-2 text-sm">
            <Mail className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
            <a
              href={`mailto:${guest.email}`}
              className="truncate text-brand-600 hover:underline dark:text-brand-400"
            >
              {guest.email}
            </a>
          </li>

          {guest.phone && (
            <li className="flex items-center gap-2 text-sm">
              <Phone className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <a
                href={`tel:${guest.phone}`}
                className="text-foreground hover:underline"
              >
                {guest.phone}
              </a>
            </li>
          )}

          {guest.country && (
            <li className="flex items-center gap-2 text-sm">
              <Globe className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <span className="text-foreground">{guest.country}</span>
            </li>
          )}

          {guest.id_type && guest.id_number && (
            <li className="flex items-start gap-2 text-sm">
              <CreditCard className="h-3.5 w-3.5 shrink-0 mt-0.5 text-muted-foreground" />
              <div>
                <span className="text-foreground">{guest.id_number}</span>
                <span className="ml-1.5 text-xs text-muted-foreground">({guest.id_type})</span>
              </div>
            </li>
          )}
        </ul>
      </CardContent>
    </Card>
  )
}
