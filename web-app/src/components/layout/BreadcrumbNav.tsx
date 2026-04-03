import { Link, useLocation, useMatches } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BreadcrumbHandle {
  breadcrumb?: string | ((params: Record<string, string>) => string)
}

const ROUTE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard', rooms: 'Rooms', 'rate-plans': 'Rate Plans',
  inventory: 'Inventory', calendar: 'Calendar', 'seasonal-rules': 'Seasonal Rules',
  reservations: 'Reservations', channels: 'Channels', mappings: 'Mappings',
  'sync-log': 'Sync Log', notifications: 'Notifications', profile: 'Profile',
  settings: 'Settings', admin: 'Admin', tenants: 'Tenants', users: 'Users',
}

function segmentToLabel(segment: string): string {
  if (/^[0-9a-f-]{36}$/i.test(segment)) return '…'
  return ROUTE_LABELS[segment] ?? segment.charAt(0).toUpperCase() + segment.slice(1)
}

export function BreadcrumbNav() {
  const location = useLocation()
  const matches = useMatches()
  const segments = location.pathname.split('/').filter(Boolean)

  if (segments.length === 0) return null

  const crumbs = segments.map((seg, idx) => {
    const href = '/' + segments.slice(0, idx + 1).join('/')
    const label = segmentToLabel(seg)
    const isLast = idx === segments.length - 1
    const match = matches.find((m) => m.pathname === href)
    const handle = match?.handle as BreadcrumbHandle | undefined
    const resolvedLabel = typeof handle?.breadcrumb === 'function'
      ? handle.breadcrumb(match?.params as Record<string, string>)
      : (handle?.breadcrumb ?? label)
    return { href, label: resolvedLabel, isLast }
  })

  return (
    <nav aria-label="Breadcrumb">
      <ol className="flex items-center gap-1 text-[13px]">
        <li>
          <Link to="/" className="text-muted-foreground/60 hover:text-foreground transition-colors" aria-label="Home">
            <Home className="h-3.5 w-3.5" />
          </Link>
        </li>
        {crumbs.map(({ href, label, isLast }) => (
          <li key={href} className="flex items-center gap-1">
            <ChevronRight className="h-3 w-3 text-muted-foreground/30" />
            {isLast ? (
              <span className="font-medium text-foreground/80">{label}</span>
            ) : (
              <Link to={href} className={cn('text-muted-foreground/60 hover:text-foreground transition-colors')}>
                {label}
              </Link>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
