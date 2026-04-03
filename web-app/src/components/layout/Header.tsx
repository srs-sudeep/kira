import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Sun, Moon, Monitor, LogOut, User, ChevronDown, Palette, Search,
  Settings,
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { useUiStore, type AccentColor } from '@/stores/ui-store'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetTrigger,
} from '@/components/ui/sheet'
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

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50 px-6">
      {/* ── Left: Search ─────────────────────────────────────────────── */}
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <div className={cn(
          'relative hidden md:flex items-center transition-all duration-200',
          searchFocused ? 'w-full max-w-md' : 'w-48 max-w-sm',
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
      </div>

      {/* ── Right: Notifications, Appearance sheet, Profile (rightmost) ─ */}
      <div className="flex shrink-0 items-center gap-1.5">
        <NotificationBell />

        <Sheet>
          <SheetTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full"
              aria-label="Appearance and theme"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </SheetTrigger>
          <SheetContent side="right" className="flex w-full flex-col sm:max-w-sm border-border">
            <SheetHeader className="text-left pr-8">
              <SheetTitle>Appearance</SheetTitle>
              <SheetDescription>
                Theme and accent color for the app.
              </SheetDescription>
            </SheetHeader>

            <div className="mt-6 flex flex-1 flex-col gap-8 overflow-y-auto pb-6">
              <div>
                <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Theme
                </p>
                <div className="grid gap-2">
                  {[
                    { value: 'light' as const, label: 'Light', icon: Sun },
                    { value: 'dark' as const, label: 'Dark', icon: Moon },
                    { value: 'system' as const, label: 'System', icon: Monitor },
                  ].map(({ value, label, icon: Icon }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setTheme(value)}
                      className={cn(
                        'flex w-full items-center gap-3 rounded-xl border px-3 py-2.5 text-left text-sm transition-colors',
                        theme === value
                          ? 'border-primary/50 bg-primary/10 text-foreground'
                          : 'border-border/60 bg-muted/20 text-muted-foreground hover:bg-muted/40 hover:text-foreground',
                      )}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span className="font-medium">{label}</span>
                      {theme === value && (
                        <span className="ml-auto text-xs font-semibold text-primary">Active</span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <p className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <Palette className="h-3.5 w-3.5" />
                  Accent color
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {ACCENT_OPTIONS.map(({ value, label, swatch }) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setAccentColor(value)}
                      className={cn(
                        'flex items-center gap-2 rounded-xl border px-3 py-2.5 text-left text-xs font-medium transition-colors',
                        accentColor === value
                          ? 'border-primary/50 bg-primary/10 text-foreground ring-1 ring-primary/30'
                          : 'border-border/60 bg-muted/20 text-muted-foreground hover:bg-muted/40',
                      )}
                    >
                      <span className={cn('h-3.5 w-3.5 shrink-0 rounded-full ring-1 ring-black/10', swatch)} />
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </SheetContent>
        </Sheet>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-muted/50 outline-none focus-visible:ring-2 focus-visible:ring-ring/30">
              <Avatar className="h-8 w-8 ring-2 ring-primary/20">
                <AvatarImage src={user?.avatar_url} alt={user?.full_name} />
                <AvatarFallback className="text-[11px] font-bold bg-gradient-to-br from-primary/20 to-primary/10 text-primary">
                  {user ? getInitials(user.full_name) : 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="hidden lg:block text-left min-w-0 max-w-[160px]">
                <div className="flex items-center gap-2">
                  <span className="text-[13px] font-semibold text-foreground truncate">
                    @{emailPrefix}
                  </span>
                  <span className="shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider text-primary dark:bg-primary/20">
                    {roleBadge}
                  </span>
                </div>
                <p className="text-[11px] text-muted-foreground truncate">
                  {user?.full_name}
                </p>
              </div>
              <ChevronDown className="hidden lg:block h-3 w-3 text-muted-foreground/60 shrink-0" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-52">
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
      </div>
    </header>
  )
}
