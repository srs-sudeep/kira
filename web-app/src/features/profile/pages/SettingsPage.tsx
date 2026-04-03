import { NavLink, Outlet } from 'react-router-dom'
import { Building2, Users, ClipboardList } from 'lucide-react'
import { cn } from '@/lib/utils'

const SETTINGS_NAV = [
  { to: '/settings', label: 'Property', icon: Building2, end: true },
  { to: '/settings/users', label: 'Users', icon: Users, end: false },
  { to: '/settings/audit-log', label: 'Audit Log', icon: ClipboardList, end: false },
]

export default function SettingsPage() {
  return (
    <div className="relative flex flex-col gap-6 p-6">
      {/* Soft backdrop behind settings */}
      <div
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_70%_50%_at_0%_0%,hsl(var(--primary)/0.06),transparent)]"
        aria-hidden
      />

      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground/75">Manage your hotel configuration and team</p>
      </div>

      <div className="flex flex-col gap-8 lg:flex-row lg:gap-10">
        <nav
          className="shrink-0 space-y-1 rounded-2xl border border-border/40 bg-card/55 p-2 shadow-lg glass backdrop-blur-xl lg:w-52"
          aria-label="Settings sections"
        >
          {SETTINGS_NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'group relative flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm transition-all duration-200',
                  isActive
                    ? 'bg-primary/12 font-medium text-primary shadow-[inset_0_0_0_1px_hsl(var(--primary)/0.2)] dark:bg-primary/18'
                    : 'text-muted-foreground hover:bg-muted/40 hover:text-foreground',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={cn(
                      'absolute left-0 top-1/2 h-6 w-1 -translate-y-1/2 rounded-full bg-primary transition-opacity duration-200',
                      isActive ? 'opacity-100' : 'opacity-0 group-hover:opacity-40',
                    )}
                    aria-hidden
                  />
                  <Icon
                    className={cn(
                      'h-4 w-4 shrink-0 transition-colors',
                      isActive ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground',
                    )}
                  />
                  <span className="pl-0.5">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="min-w-0 flex-1 rounded-2xl border border-border/30 bg-card/40 p-1 shadow-sm glass backdrop-blur-md lg:p-0 lg:border-0 lg:bg-transparent lg:shadow-none lg:backdrop-blur-none">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
