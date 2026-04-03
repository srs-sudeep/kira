import * as React from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { DayPicker } from 'react-day-picker'
import { cn } from '@/lib/utils'
import 'react-day-picker/style.css'

export type CalendarProps = React.ComponentProps<typeof DayPicker>

function Calendar({ className, classNames, showOutsideDays = true, components, ...props }: CalendarProps) {
  return (
    <DayPicker
      showOutsideDays={showOutsideDays}
      className={cn('p-3', className)}
      classNames={{
        root: 'rdp-root',
        months: 'flex flex-col gap-4 sm:flex-row',
        month: 'space-y-4',
        month_caption: 'flex justify-center pt-1 relative items-center',
        caption_label: 'text-sm font-medium',
        nav: 'flex items-center gap-1',
        button_previous: cn('absolute left-1 inline-flex h-7 w-7 items-center justify-center rounded-lg border border-border/40 bg-muted/30 opacity-80 hover:opacity-100 hover:bg-muted/50 transition-all'),
        button_next: cn('absolute right-1 inline-flex h-7 w-7 items-center justify-center rounded-lg border border-border/40 bg-muted/30 opacity-80 hover:opacity-100 hover:bg-muted/50 transition-all'),
        month_grid: 'w-full border-collapse',
        weekdays: 'flex',
        weekday: 'w-8 text-[0.8rem] font-normal text-muted-foreground/70 text-center',
        week: 'mt-2 flex w-full',
        day: 'relative h-8 w-full p-0 text-center text-sm',
        day_button: cn('inline-flex h-8 w-8 items-center justify-center rounded-lg p-0 font-normal transition-all', 'hover:bg-accent/50 hover:text-accent-foreground', 'focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring/30'),
        selected: 'bg-primary text-primary-foreground hover:bg-primary hover:text-primary-foreground shadow-sm',
        today: 'bg-accent/40 text-accent-foreground font-semibold',
        outside: 'text-muted-foreground/40',
        disabled: 'text-muted-foreground/30',
        range_middle: 'rounded-none bg-accent/20',
        range_start: 'rounded-r-none bg-primary text-primary-foreground',
        range_end: 'rounded-l-none bg-primary text-primary-foreground',
        hidden: 'invisible',
        ...classNames,
      }}
      components={{
        Chevron: ({ orientation }) => orientation === 'left' ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />,
        ...components,
      }}
      {...props}
    />
  )
}
Calendar.displayName = 'Calendar'

export { Calendar }
