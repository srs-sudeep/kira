import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold transition-colors',
  {
    variants: {
      variant: {
        default: 'bg-primary/15 text-primary dark:bg-primary/20 dark:text-primary',
        secondary: 'bg-secondary text-secondary-foreground',
        destructive: 'bg-destructive/15 text-destructive dark:bg-destructive/20',
        outline: 'border border-border/40 text-foreground/80',
        success: 'bg-accent-500/15 text-accent-600 dark:bg-accent-500/20 dark:text-accent-400',
        warning: 'bg-warm-500/15 text-warm-600 dark:bg-warm-500/20 dark:text-warm-400',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />
}

export { Badge, badgeVariants }
