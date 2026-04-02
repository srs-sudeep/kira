import { type LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface KpiCardProps {
  title: string
  value: string | number
  change?: number        // percentage change, e.g. 12.5 = +12.5 %
  changeLabel?: string   // e.g. "vs last 30 days"
  icon: LucideIcon
  iconClassName?: string
  format?: 'number' | 'currency' | 'percent'
  isLoading?: boolean
}

function TrendIcon({ change }: { change: number }) {
  if (change > 0) return <TrendingUp className="h-3.5 w-3.5" />
  if (change < 0) return <TrendingDown className="h-3.5 w-3.5" />
  return <Minus className="h-3.5 w-3.5" />
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
  const isNeutral = (change ?? 0) === 0

  return (
    <Card>
      <CardContent className="p-6">
        {isLoading ? (
          <div className="space-y-3">
            <div className="h-4 w-24 animate-pulse rounded bg-muted" />
            <div className="h-8 w-32 animate-pulse rounded bg-muted" />
            <div className="h-3 w-20 animate-pulse rounded bg-muted" />
          </div>
        ) : (
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm font-medium text-muted-foreground">{title}</p>
              <p className="text-2xl font-bold tabular-nums text-foreground">{value}</p>

              {change !== undefined && (
                <div
                  className={cn(
                    'flex items-center gap-1 text-xs font-medium',
                    isPositive && 'text-accent-600 dark:text-accent-400',
                    isNegative && 'text-destructive',
                    isNeutral && 'text-muted-foreground',
                  )}
                >
                  <TrendIcon change={change} />
                  <span>
                    {isPositive ? '+' : ''}
                    {change.toFixed(1)}%
                  </span>
                  <span className="text-muted-foreground font-normal">{changeLabel}</span>
                </div>
              )}
            </div>

            <div
              className={cn(
                'flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-muted',
                iconClassName,
              )}
            >
              <Icon className="h-5 w-5 text-muted-foreground" />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
