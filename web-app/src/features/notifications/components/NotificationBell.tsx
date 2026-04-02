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

  // Trigger pulse animation when count increases
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
                'absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center',
                'rounded-full bg-brand-600 px-1 text-[10px] font-bold leading-none text-white',
              )}
            >
              {count > 99 ? '99+' : count}
            </span>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        sideOffset={8}
        className="w-auto p-0 shadow-xl"
      >
        <NotificationDropdown onClose={() => setOpen(false)} />
      </PopoverContent>
    </Popover>
  )
}
