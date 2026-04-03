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
  Hotel,
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
  children?: NavItem[]
}

const NAV_ITEMS: NavItem[] = [
  {
    label: 'Dashboard',
    href: ROUTES.DASHBOARD,
    icon: LayoutDashboard,
  },
  {
    label: 'Rooms',
    href: ROUTES.ROOMS,
    icon: BedDouble,
    allowedRoles: [USER_ROLES.PROPERTY_OWNER, USER_ROLES.REVENUE_MANAGER, USER_ROLES.SUPER_ADMIN],
  },
  {
    label: 'Inventory',
    href: ROUTES.INVENTORY_CALENDAR,
    icon: CalendarDays,
  },
  {
    label: 'Reservations',
    href: ROUTES.RESERVATIONS,
    icon: BookOpen,
  },
  {
    label: 'Channels',
    href: ROUTES.CHANNELS,
    icon: Radio,
    allowedRoles: [USER_ROLES.PROPERTY_OWNER, USER_ROLES.REVENUE_MANAGER, USER_ROLES.SUPER_ADMIN],
  },
  {
    label: 'Notifications',
    href: ROUTES.NOTIFICATIONS,
    icon: Bell,
  },
]

const ADMIN_NAV_ITEMS: NavItem[] = [
  {
    label: 'Tenants',
    href: ROUTES.ADMIN_TENANTS,
    icon: Building2,
    allowedRoles: [USER_ROLES.SUPER_ADMIN],
  },
  {
    label: 'Users',
    href: ROUTES.ADMIN_USERS,
    icon: Users,
    allowedRoles: [USER_ROLES.SUPER_ADMIN],
  },
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

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex flex-col border-r bg-card transition-all duration-200',
        sidebarCollapsed ? 'w-16' : 'w-64',
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-4">
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Hotel className="h-4 w-4" />
          </div>
          {!sidebarCollapsed && (
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">KIRA</p>
              <p className="truncate text-xs text-muted-foreground">Channel Manager</p>
            </div>
          )}
        </div>
      </div>

      {/* Main nav */}
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-2">
          {NAV_ITEMS.filter(isAllowed).map((item) => (
            <li key={item.href}>
              <NavLink
                to={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive(item.href)
                    ? 'bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  sidebarCollapsed && 'justify-center px-2',
                )}
                title={sidebarCollapsed ? item.label : undefined}
              >
                <item.icon className="h-4 w-4 shrink-0" />
                {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
              </NavLink>
            </li>
          ))}
        </ul>

        {/* Admin section */}
        {user?.role === USER_ROLES.SUPER_ADMIN && (
          <div className="mt-4">
            {!sidebarCollapsed && (
              <p className="mb-1 px-5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Admin
              </p>
            )}
            <ul className="space-y-1 px-2">
              {ADMIN_NAV_ITEMS.filter(isAllowed).map((item) => (
                <li key={item.href}>
                  <NavLink
                    to={item.href}
                    className={cn(
                      'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                      isActive(item.href)
                        ? 'bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300'
                        : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                      sidebarCollapsed && 'justify-center px-2',
                    )}
                    title={sidebarCollapsed ? item.label : undefined}
                  >
                    <item.icon className="h-4 w-4 shrink-0" />
                    {!sidebarCollapsed && <span className="truncate">{item.label}</span>}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        )}
      </nav>

      {/* Settings + collapse toggle */}
      <div className="border-t p-2 space-y-1">
        <NavLink
          to={ROUTES.SETTINGS}
          className={cn(
            'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground',
            sidebarCollapsed && 'justify-center px-2',
          )}
          title={sidebarCollapsed ? 'Settings' : undefined}
        >
          <Settings className="h-4 w-4 shrink-0" />
          {!sidebarCollapsed && <span>Settings</span>}
        </NavLink>

        <button
          onClick={toggleSidebar}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {sidebarCollapsed ? (
            <ChevronRight className="h-4 w-4 shrink-0 mx-auto" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 shrink-0" />
              <span>Collapse</span>
            </>
          )}
        </button>
      </div>
    </aside>
  )
}
