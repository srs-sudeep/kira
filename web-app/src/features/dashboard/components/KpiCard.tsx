import { type LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import { SkeletonPulse } from '@/components/shared/LoadingState'

interface KpiCardProps {
  title: string
  value: string | number
  change?: number
  changeLabel?: string
  icon: LucideIcon
  iconClassName?: string
  isLoading?: boolean
}

function TrendIcon({ change }: { change: number }) {
  if (change > 0) return <TrendingUp className="h-3 w-3" />
  if (change < 0) return <TrendingDown className="h-3 w-3" />
  return <Minus className="h-3 w-3" />
}

export function KpiCard({
  title,
  value,
  change,
  changeLabel = 'vs last period',
  icon: Icon,
  iconClassName,
  isLoading,
}: KpiCardProps) {
  const isPositive = (change ?? 0) > 0
  const isNegative = (change ?? 0) < 0

  return (
    <div className="group edge-light p-5">
      <div>
        {isLoading ? (
          <div className="space-y-3">
            <SkeletonPulse className="h-3.5 w-24" />
            <SkeletonPulse className="h-7 w-32" />
            <SkeletonPulse className="h-3 w-20" />
          </div>
        ) : (
          <div className="flex items-start justify-between">
            <div className="space-y-1.5">
              <p className="text-[13px] font-medium text-muted-foreground">{title}</p>
              <p className="text-2xl font-bold tabular-nums tracking-tight text-foreground">{value}</p>

              {change !== undefined && (
                <div
                  className={cn(
                    'flex items-center gap-1 text-[11px] font-semibold',
                    isPositive && 'text-accent-500',
                    isNegative && 'text-rose-500',
                    !isPositive && !isNegative && 'text-muted-foreground',
                  )}
                >
                  <TrendIcon change={change} />
                  <span>
                    {isPositive ? '+' : ''}
                    {change.toFixed(1)}%
                  </span>
                  <span className="text-muted-foreground/70 font-normal">{changeLabel}</span>
                </div>
              )}
            </div>

            <div
              className={cn(
                'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl',
                iconClassName ?? 'bg-brand-50 dark:bg-brand-950/40',
              )}
            >
              <Icon className="h-5 w-5 text-brand-500 dark:text-brand-400" />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
