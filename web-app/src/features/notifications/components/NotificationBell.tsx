import { useState, useRef, useEffect } from 'react'
import { Bell } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { cn } from '@/lib/utils'
import { QUERY_KEYS } from '@/config/constants'
import notificationsService from '../services/notifications-service'
import { NotificationDropdown } from './NotificationDropdown'

export function NotificationBell() {
  const [open, setOpen] = useState(false)
  const prevCount = useRef(0)
  const [pulse, setPulse] = useState(false)

  const { data: count = 0 } = useQuery({
    queryKey: QUERY_KEYS.NOTIFICATIONS.UNREAD_COUNT,
    queryFn: notificationsService.getUnreadCount,
    refetchInterval: 30_000,
    staleTime: 20_000,
  })

  useEffect(() => {
    if (count > prevCount.current && prevCount.current !== 0) {
      setPulse(true)
      const t = setTimeout(() => setPulse(false), 1000)
      return () => clearTimeout(t)
    }
    prevCount.current = count
  }, [count])

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-9 w-9"
          aria-label={`Notifications${count > 0 ? ` — ${count} unread` : ''}`}
        >
          <Bell className={cn('h-4 w-4 transition-transform', pulse && 'animate-bounce')} />
          {count > 0 && (
            <span
              className={cn(
                'absolute right-0.5 top-0.5 flex h-[18px] min-w-[18px] items-center justify-center rounded-full',
                'bg-primary px-1 text-[10px] font-bold leading-none text-primary-foreground',
                'animate-pulse shadow-[0_0_0_2px_hsl(var(--background)),0_0_14px_hsl(var(--primary)/0.65)]',
              )}
            >
              {count > 99 ? '99+' : count}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" sideOffset={8} className="w-auto border-border/25 bg-transparent p-0 shadow-none">
        <NotificationDropdown onClose={() => setOpen(false)} />
      </PopoverContent>
    </Popover>
  )
}
