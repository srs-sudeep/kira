import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Building2, Users, ClipboardList } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEffect } from 'react'

const SETTINGS_NAV = [
  { to: '/settings', label: 'Property', icon: Building2, end: true },
  { to: '/settings/users', label: 'Users', icon: Users, end: false },
  { to: '/settings/audit-log', label: 'Audit Log', icon: ClipboardList, end: false },
]

export default function SettingsPage() {
  const location = useLocation()
  const navigate = useNavigate()

  // Redirect /settings → /settings (property) — handled by index route, but guard here too
  useEffect(() => {
    if (location.pathname === '/settings') {
      // already at root, handled by nested index route
    }
  }, [location.pathname, navigate])

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground">Manage your hotel configuration and team</p>
      </div>

      <div className="flex gap-8">
        {/* Side nav */}
        <nav className="shrink-0 w-44 space-y-1">
          {SETTINGS_NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors',
                  isActive
                    ? 'bg-brand-50 text-brand-700 font-medium dark:bg-brand-950/40 dark:text-brand-400'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
