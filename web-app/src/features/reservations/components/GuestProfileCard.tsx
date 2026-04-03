import { Mail, Phone, Globe, CreditCard } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { cn, getInitials } from '@/lib/utils'
import type { Guest } from '@/types/reservation'

interface Props {
  guest: Guest
  pastStays?: number
}

const iconBadge = (variant: 'mail' | 'phone' | 'globe' | 'card') =>
  cn(
    'flex h-8 w-8 shrink-0 items-center justify-center rounded-xl shadow-inner ring-1 ring-white/20 dark:ring-white/10',
    variant === 'mail' &&
      'bg-gradient-to-br from-sky-400/25 via-primary/15 to-blue-600/20 text-sky-700 dark:text-sky-300',
    variant === 'phone' &&
      'bg-gradient-to-br from-emerald-400/25 via-emerald-500/10 to-teal-600/20 text-emerald-700 dark:text-emerald-300',
    variant === 'globe' &&
      'bg-gradient-to-br from-violet-400/25 via-accent-500/15 to-fuchsia-600/20 text-violet-700 dark:text-violet-300',
    variant === 'card' &&
      'bg-gradient-to-br from-amber-400/25 via-orange-500/10 to-rose-600/20 text-amber-800 dark:text-amber-200',
  )

export function GuestProfileCard({ guest, pastStays }: Props) {
  const fullName = `${guest.first_name} ${guest.last_name}`

  return (
    <Card className="overflow-hidden border-border/40 bg-card/75 glass shadow-lg transition-shadow hover:shadow-xl">
      <CardHeader className="border-b border-border/30 bg-gradient-to-r from-primary/[0.06] via-transparent to-accent-500/[0.08] pb-3 backdrop-blur-sm dark:from-primary/10 dark:to-accent-500/10">
        <CardTitle className="text-sm font-medium tracking-wide text-muted-foreground">Guest</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-gradient-to-br from-primary/30 via-accent-500/20 to-primary/30 p-[3px] shadow-sm ring-2 ring-primary/15 dark:from-primary/40 dark:via-accent-500/25 dark:to-primary/35">
            <Avatar className="h-11 w-11 ring-0">
              <AvatarFallback className="bg-gradient-to-br from-primary/15 to-accent-500/15 text-sm font-semibold text-primary dark:from-primary/25 dark:to-accent-500/25">
                {getInitials(fullName)}
              </AvatarFallback>
            </Avatar>
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-foreground">{fullName}</p>
            {pastStays !== undefined && (
              <p className="text-xs text-muted-foreground/70">
                {pastStays} past stay{pastStays !== 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>
        <ul className="space-y-2.5">
          <li className="flex items-center gap-3 text-sm">
            <span className={iconBadge('mail')}>
              <Mail className="h-3.5 w-3.5" />
            </span>
            <a href={`mailto:${guest.email}`} className="truncate text-primary hover:underline">
              {guest.email}
            </a>
          </li>
          {guest.phone && (
            <li className="flex items-center gap-3 text-sm">
              <span className={iconBadge('phone')}>
                <Phone className="h-3.5 w-3.5" />
              </span>
              <a href={`tel:${guest.phone}`} className="text-foreground hover:underline">
                {guest.phone}
              </a>
            </li>
          )}
          {guest.country && (
            <li className="flex items-center gap-3 text-sm">
              <span className={iconBadge('globe')}>
                <Globe className="h-3.5 w-3.5" />
              </span>
              <span className="text-foreground">{guest.country}</span>
            </li>
          )}
          {guest.id_type && guest.id_number && (
            <li className="flex items-start gap-3 text-sm">
              <span className={cn(iconBadge('card'), 'mt-0.5')}>
                <CreditCard className="h-3.5 w-3.5" />
              </span>
              <div>
                <span className="font-mono text-xs text-foreground">{guest.id_number}</span>
                <span className="ml-1.5 text-xs text-muted-foreground/60">({guest.id_type})</span>
              </div>
            </li>
          )}
        </ul>
      </CardContent>
    </Card>
  )
}
