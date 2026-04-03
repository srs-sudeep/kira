import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  BedDouble,
  CalendarDays,
  BookOpen,
  Radio,
  Bell,
  Settings,
  Users,
  Building2,
  ChevronLeft,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useUiStore } from '@/stores/ui-store'
import { useAuthStore } from '@/stores/auth-store'
import { ROUTES } from '@/router/routes'
import { USER_ROLES } from '@/config/constants'
import type { UserRole } from '@/config/constants'

interface NavItem {
  label: string
  href: string
  icon: React.ElementType
  allowedRoles?: UserRole[]
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard',     href: ROUTES.DASHBOARD,          icon: LayoutDashboard },
  { label: 'Rooms',         href: ROUTES.ROOMS,              icon: BedDouble,
    allowedRoles: [USER_ROLES.PROPERTY_OWNER, USER_ROLES.REVENUE_MANAGER, USER_ROLES.SUPER_ADMIN] },
  { label: 'Inventory',     href: ROUTES.INVENTORY_CALENDAR, icon: CalendarDays },
  { label: 'Reservations',  href: ROUTES.RESERVATIONS,       icon: BookOpen },
  { label: 'Channels',      href: ROUTES.CHANNELS,           icon: Radio,
    allowedRoles: [USER_ROLES.PROPERTY_OWNER, USER_ROLES.REVENUE_MANAGER, USER_ROLES.SUPER_ADMIN] },
  { label: 'Notifications', href: ROUTES.NOTIFICATIONS,      icon: Bell },
]

const ADMIN_NAV_ITEMS: NavItem[] = [
  { label: 'Tenants', href: ROUTES.ADMIN_TENANTS, icon: Building2, allowedRoles: [USER_ROLES.SUPER_ADMIN] },
  { label: 'Users',   href: ROUTES.ADMIN_USERS,   icon: Users,     allowedRoles: [USER_ROLES.SUPER_ADMIN] },
]

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUiStore()
  const user = useAuthStore((s) => s.user)
  const location = useLocation()

  function isAllowed(item: NavItem) {
    if (!item.allowedRoles) return true
    return user ? item.allowedRoles.includes(user.role) : false
  }

  function isActive(href: string) {
    return location.pathname === href || location.pathname.startsWith(`${href}/`)
  }

  const collapsed = sidebarCollapsed

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex flex-col',
        'bg-sidebar/80 glass border-r border-sidebar-border',
        'transition-all duration-300 ease-in-out',
        collapsed ? 'w-[72px]' : 'w-[272px]',
      )}
    >
      {/* ── Brand ──────────────────────────────────────────────────────── */}
      <div className={cn(
        'flex h-16 items-center gap-3 border-b border-sidebar-border px-4',
        collapsed && 'justify-center px-2',
      )}>
        <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 shadow-lg shadow-brand-500/25">
          <Sparkles className="h-4.5 w-4.5 text-white" />
          <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full border-2 border-sidebar bg-accent-400" />
        </div>
        {!collapsed && (
          <div className="min-w-0 overflow-hidden">
            <p className="truncate text-[15px] font-bold tracking-tight text-sidebar-foreground">
              KIRA
            </p>
            <p className="truncate text-[11px] font-medium text-muted-foreground">
              Channel Manager
            </p>
          </div>
        )}
      </div>

      {/* ── Main nav ───────────────────────────────────────────────────── */}
      <nav className="flex-1 overflow-y-auto px-3 py-4">
        {!collapsed && (
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70">
            Navigation
          </p>
        )}

        <ul className="space-y-0.5">
          {NAV_ITEMS.filter(isAllowed).map((item) => {
            const active = isActive(item.href)
            return (
              <li key={item.href}>
                <NavLink
                  to={item.href}
                  className={cn(
                    'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150',
                    active
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
                    collapsed && 'justify-center px-0',
                  )}
                  title={collapsed ? item.label : undefined}
                >
                  {active && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-full bg-brand-500" />
                  )}
                  <item.icon className={cn(
                    'h-[18px] w-[18px] shrink-0 transition-colors',
                    active ? 'text-brand-500' : 'group-hover:text-sidebar-foreground',
                  )} />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </NavLink>
              </li>
            )
          })}
        </ul>

        {/* Admin section */}
        {user?.role === USER_ROLES.SUPER_ADMIN && (
          <div className="mt-6">
            {!collapsed && (
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70">
                Administration
              </p>
            )}
            <ul className="space-y-0.5">
              {ADMIN_NAV_ITEMS.filter(isAllowed).map((item) => {
                const active = isActive(item.href)
                return (
                  <li key={item.href}>
                    <NavLink
                      to={item.href}
                      className={cn(
                        'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150',
                        active
                          ? 'bg-sidebar-accent text-sidebar-accent-foreground shadow-sm'
                          : 'text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
                        collapsed && 'justify-center px-0',
                      )}
                      title={collapsed ? item.label : undefined}
                    >
                      {active && (
                        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-[3px] rounded-full bg-brand-500" />
                      )}
                      <item.icon className={cn(
                        'h-[18px] w-[18px] shrink-0 transition-colors',
                        active ? 'text-brand-500' : 'group-hover:text-sidebar-foreground',
                      )} />
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </NavLink>
                  </li>
                )
              })}
            </ul>
          </div>
        )}
      </nav>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <div className="border-t border-sidebar-border p-3 space-y-0.5">
        <NavLink
          to={ROUTES.SETTINGS}
          className={cn(
            'group flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-all duration-150 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
            isActive(ROUTES.SETTINGS) && 'bg-sidebar-accent text-sidebar-accent-foreground',
            collapsed && 'justify-center px-0',
          )}
          title={collapsed ? 'Settings' : undefined}
        >
          <Settings className="h-[18px] w-[18px] shrink-0" />
          {!collapsed && <span>Settings</span>}
        </NavLink>

        <button
          onClick={toggleSidebar}
          className={cn(
            'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-all duration-150 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground',
            collapsed && 'justify-center px-0',
          )}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <ChevronRight className="h-[18px] w-[18px] shrink-0" />
          ) : (
            <>
              <ChevronLeft className="h-[18px] w-[18px] shrink-0" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
