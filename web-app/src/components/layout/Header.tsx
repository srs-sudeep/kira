import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Sun, Moon, Monitor, LogOut, User, ChevronDown, Palette, Search,
  Settings, Plus,
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { useUiStore, type AccentColor } from '@/stores/ui-store'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
  DropdownMenuSub, DropdownMenuSubTrigger, DropdownMenuSubContent,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { NotificationBell } from '@/features/notifications/components/NotificationBell'
import { ROUTES } from '@/router/routes'
import { cn, getInitials } from '@/lib/utils'

const ACCENT_OPTIONS: { value: AccentColor; label: string; swatch: string }[] = [
  { value: 'indigo',  label: 'Indigo',  swatch: 'bg-indigo-500' },
  { value: 'blue',    label: 'Blue',    swatch: 'bg-blue-500' },
  { value: 'violet',  label: 'Violet',  swatch: 'bg-violet-500' },
  { value: 'rose',    label: 'Rose',    swatch: 'bg-rose-500' },
  { value: 'emerald', label: 'Emerald', swatch: 'bg-emerald-500' },
  { value: 'amber',   label: 'Amber',   swatch: 'bg-amber-500' },
]

const ROLE_LABELS: Record<string, string> = {
  SUPER_ADMIN: 'ADMIN',
  PROPERTY_OWNER: 'OWNER',
  REVENUE_MANAGER: 'MANAGER',
  READ_ONLY: 'VIEWER',
}

export function Header() {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const { theme, setTheme, accentColor, setAccentColor } = useUiStore()
  const [searchFocused, setSearchFocused] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  function handleLogout() {
    logout()
    navigate(ROUTES.LOGIN, { replace: true })
  }

  const emailPrefix = user?.email?.split('@')[0] ?? 'user'
  const roleBadge = ROLE_LABELS[user?.role ?? ''] ?? 'USER'

  const themeIcon = theme === 'dark' ? Moon : theme === 'light' ? Sun : Monitor

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50 px-6">
      {/* ── Left: User Profile ─────────────────────────────────────────── */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="flex items-center gap-3 rounded-lg px-2 py-1.5 -ml-2 transition-colors hover:bg-muted/50 outline-none focus-visible:ring-2 focus-visible:ring-ring/30">
            <Avatar className="h-8 w-8 ring-2 ring-primary/20">
              <AvatarImage src={user?.avatar_url} alt={user?.full_name} />
              <AvatarFallback className="text-[11px] font-bold bg-gradient-to-br from-primary/20 to-primary/10 text-primary">
                {user ? getInitials(user.full_name) : 'U'}
              </AvatarFallback>
            </Avatar>
            <div className="hidden md:block text-left min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-foreground truncate">
                  @{emailPrefix}
                </span>
                <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-primary dark:bg-primary/20">
                  {roleBadge}
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground truncate max-w-[140px]">
                {user?.full_name}
              </p>
            </div>
            <ChevronDown className="hidden md:block h-3 w-3 text-muted-foreground/60" />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-52">
          <DropdownMenuLabel className="font-normal">
            <p className="text-sm font-semibold">{user?.full_name}</p>
            <p className="text-[11px] text-muted-foreground truncate">{user?.email}</p>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem className="gap-2 text-xs" onClick={() => navigate(ROUTES.PROFILE)}>
            <User className="h-3.5 w-3.5" />
            Profile
          </DropdownMenuItem>
          <DropdownMenuItem className="gap-2 text-xs" onClick={() => navigate(ROUTES.SETTINGS)}>
            <Settings className="h-3.5 w-3.5" />
            Settings
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem
            className="gap-2 text-xs text-destructive focus:text-destructive"
            onClick={handleLogout}
          >
            <LogOut className="h-3.5 w-3.5" />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* ── Center: Primary CTA ────────────────────────────────────────── */}
      <Button
        onClick={() => navigate(ROUTES.RESERVATIONS)}
        className="hidden sm:inline-flex rounded-full px-5 gap-2 bg-primary text-primary-foreground shadow-md hover:shadow-[0_0_20px_hsl(var(--primary)/0.4)] transition-shadow"
      >
        New Booking
        <Plus className="h-4 w-4" />
      </Button>

      {/* ── Right: Tools ───────────────────────────────────────────────── */}
      <div className="flex items-center gap-1.5">
        {/* Search */}
        <div className={cn(
          'relative hidden md:flex items-center transition-all duration-200',
          searchFocused ? 'w-64' : 'w-48',
        )}>
          <Search className="absolute left-3 h-3.5 w-3.5 text-muted-foreground/60" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            placeholder="Search..."
            className="h-8 w-full rounded-lg border border-border bg-muted/40 pl-9 pr-10 text-xs text-foreground placeholder:text-muted-foreground/50 outline-none transition-all focus:border-primary/40 focus:bg-background focus:ring-2 focus:ring-primary/10 dark:bg-muted/20"
          />
          {!searchFocused && (
            <kbd className="absolute right-2.5 flex items-center gap-0.5 rounded border border-border bg-muted/60 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground/70">
              <span className="text-[9px]">&#8984;</span>/
            </kbd>
          )}
        </div>

        <NotificationBell />

        {/* Settings / Theme / Accent dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full" aria-label="Settings">
              <Settings className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="text-[11px]">Appearance</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuSub>
              <DropdownMenuSubTrigger className="gap-2 text-xs">
                {(() => { const I = themeIcon; return <I className="h-3.5 w-3.5" /> })()}
                Theme
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                {[
                  { value: 'light' as const, label: 'Light', icon: Sun },
                  { value: 'dark' as const, label: 'Dark', icon: Moon },
                  { value: 'system' as const, label: 'System', icon: Monitor },
                ].map(({ value, label, icon: Icon }) => (
                  <DropdownMenuItem
                    key={value}
                    onClick={() => setTheme(value)}
                    className="gap-2 text-xs"
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {label}
                    {theme === value && (
                      <span className="ml-auto text-[10px] text-primary font-semibold">On</span>
                    )}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuSubContent>
            </DropdownMenuSub>
            <DropdownMenuSub>
              <DropdownMenuSubTrigger className="gap-2 text-xs">
                <Palette className="h-3.5 w-3.5" />
                Accent
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent>
                {ACCENT_OPTIONS.map(({ value, label, swatch }) => (
                  <DropdownMenuItem
                    key={value}
                    onClick={() => setAccentColor(value)}
                    className="gap-2.5 text-xs"
                  >
                    <span className={cn('h-3 w-3 rounded-full ring-1 ring-black/10', swatch)} />
                    {label}
                    {accentColor === value && (
                      <span className="ml-auto text-[10px] text-primary font-semibold">Active</span>
                    )}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
