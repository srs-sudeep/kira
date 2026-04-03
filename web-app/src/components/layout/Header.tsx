import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Sun, Moon, Monitor, LogOut, User, ChevronDown, Palette, Search,
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { useUiStore, type AccentColor } from '@/stores/ui-store'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { BreadcrumbNav } from './BreadcrumbNav'
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

  const themeOptions = [
    { value: 'light' as const, label: 'Light', icon: Sun },
    { value: 'dark' as const, label: 'Dark', icon: Moon },
    { value: 'system' as const, label: 'System', icon: Monitor },
  ]

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-border/60 bg-card/50 glass px-5">
      <div className="flex items-center gap-4 min-w-0">
        <BreadcrumbNav />
      </div>

      <div className="flex items-center gap-1.5">
        {/* Search */}
        <div className={cn(
          'relative hidden md:flex items-center transition-all duration-200',
          searchFocused ? 'w-72' : 'w-56',
        )}>
          <Search className="absolute left-3 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            placeholder="Search..."
            className="h-8 w-full rounded-lg border border-border/60 bg-muted/50 pl-9 pr-3 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none transition-all focus:border-primary/40 focus:bg-background focus:ring-2 focus:ring-primary/10"
          />
          {!searchFocused && (
            <kbd className="absolute right-2.5 rounded border border-border/60 bg-muted/70 px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
              /
            </kbd>
          )}
        </div>

        {/* Accent color picker */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Change accent color">
              <Palette className="h-3.5 w-3.5" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <DropdownMenuLabel className="text-[11px]">Accent Color</DropdownMenuLabel>
            <DropdownMenuSeparator />
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
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Theme toggle */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Toggle theme">
              {theme === 'light' && <Sun className="h-3.5 w-3.5" />}
              {theme === 'dark' && <Moon className="h-3.5 w-3.5" />}
              {theme === 'system' && <Monitor className="h-3.5 w-3.5" />}
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-36">
            {themeOptions.map(({ value, label, icon: Icon }) => (
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
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Notifications bell */}
        <NotificationBell />

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 px-2 h-8">
              <Avatar className="h-6 w-6">
                <AvatarImage src={user?.avatar_url} alt={user?.full_name} />
                <AvatarFallback className="text-[10px] font-semibold bg-brand-100 text-brand-700 dark:bg-brand-900 dark:text-brand-300">
                  {user ? getInitials(user.full_name) : 'U'}
                </AvatarFallback>
              </Avatar>
              <span className="hidden text-xs font-medium md:block max-w-[100px] truncate">
                {user?.full_name}
              </span>
              <ChevronDown className="h-3 w-3 text-muted-foreground" />
            </Button>
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
