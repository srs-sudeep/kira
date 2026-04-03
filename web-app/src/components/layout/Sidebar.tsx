import { useState } from 'react'
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
  ChevronDown,
  Sparkles,
  Activity,
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

const QUICK_STATS = [
  { label: 'Booking.com', status: 'synced' as const },
  { label: 'Expedia',     status: 'synced' as const },
  { label: 'Airbnb',      status: 'pending' as const },
  { label: 'Agoda',       status: 'error' as const },
]

const STATUS_DOT: Record<string, string> = {
  synced:  'bg-emerald-500',
  pending: 'bg-amber-500',
  error:   'bg-rose-500',
}

function SidebarNavItem({ item, active, collapsed }: { item: NavItem; active: boolean; collapsed: boolean }) {
  return (
    <li>
      <NavLink
        to={item.href}
        className={cn(
          'group relative flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150',
          active
            ? 'bg-primary/10 text-primary border-l-2 border-primary dark:bg-primary/15'
            : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground border-l-2 border-transparent',
          collapsed && 'justify-center px-0 border-l-0',
        )}
        title={collapsed ? item.label : undefined}
      >
        <item.icon className={cn(
          'h-[18px] w-[18px] shrink-0 transition-colors',
          active ? 'text-primary' : 'group-hover:text-foreground',
        )} />
        {!collapsed && <span className="truncate">{item.label}</span>}
      </NavLink>
    </li>
  )
}

export function Sidebar() {
  const { sidebarCollapsed, toggleSidebar } = useUiStore()
  const user = useAuthStore((s) => s.user)
  const location = useLocation()
  const [quickStatsOpen, setQuickStatsOpen] = useState(true)

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
        'bg-sidebar/80 glass border-r border-border',
        'transition-all duration-300 ease-in-out',
        collapsed ? 'w-[72px]' : 'w-[272px]',
      )}
    >
      {/* ── Brand ──────────────────────────────────────────────────────── */}
      <div className={cn(
        'flex h-14 items-center gap-3 border-b border-border px-4',
        collapsed && 'justify-center px-2',
      )}>
        <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/70 shadow-lg shadow-primary/25">
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
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
            Navigation
          </p>
        )}

        <ul className="space-y-0.5">
          {NAV_ITEMS.filter(isAllowed).map((item) => (
            <SidebarNavItem
              key={item.href}
              item={item}
              active={isActive(item.href)}
              collapsed={collapsed}
            />
          ))}
        </ul>

        {/* Admin section */}
        {user?.role === USER_ROLES.SUPER_ADMIN && (
          <div className="mt-6">
            {!collapsed && (
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
                Administration
              </p>
            )}
            <ul className="space-y-0.5">
              {ADMIN_NAV_ITEMS.filter(isAllowed).map((item) => (
                <SidebarNavItem
                  key={item.href}
                  item={item}
                  active={isActive(item.href)}
                  collapsed={collapsed}
                />
              ))}
            </ul>
          </div>
        )}

        {/* ── Quick Stats accordion ──────────────────────────────────── */}
        {!collapsed && (
          <div className="mt-6">
            <button
              onClick={() => setQuickStatsOpen((o) => !o)}
              className="flex w-full items-center justify-between px-3 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60 hover:text-muted-foreground transition-colors"
            >
              <span className="flex items-center gap-2">
                <Activity className="h-3 w-3" />
                Quick Stats
              </span>
              <span className="flex items-center gap-1.5">
                <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] font-bold text-primary dark:bg-primary/20">
                  {QUICK_STATS.length}
                </span>
                <ChevronDown className={cn(
                  'h-3 w-3 transition-transform duration-200',
                  quickStatsOpen && 'rotate-180',
                )} />
              </span>
            </button>

            {quickStatsOpen && (
              <ul className="mt-1 space-y-0.5">
                {QUICK_STATS.map((ch) => (
                  <li
                    key={ch.label}
                    className="flex items-center gap-3 rounded-lg px-3 py-1.5 text-[12px] text-muted-foreground"
                  >
                    <span className={cn('h-2 w-2 shrink-0 rounded-full', STATUS_DOT[ch.status])} />
                    <span className="truncate">{ch.label}</span>
                    <span className="ml-auto text-[10px] capitalize text-muted-foreground/60">
                      {ch.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </nav>

      {/* ── Footer ─────────────────────────────────────────────────────── */}
      <div className="border-t border-border p-3 space-y-0.5">
        <NavLink
          to={ROUTES.SETTINGS}
          className={cn(
            'group flex items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium transition-all duration-150',
            isActive(ROUTES.SETTINGS)
              ? 'bg-primary/10 text-primary dark:bg-primary/15'
              : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground',
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
            'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-[13px] font-medium text-muted-foreground transition-all duration-150 hover:bg-muted/50 hover:text-foreground',
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
