import { cn, formatCurrency } from '@/lib/utils'

interface CurrencyDisplayProps {
  amount: number
  currency?: string
  locale?: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
  showSign?: boolean
}

export function CurrencyDisplay({ amount, currency = 'INR', locale = 'en-IN', className, size = 'md', showSign }: CurrencyDisplayProps) {
  const formatted = formatCurrency(Math.abs(amount), currency, locale)
  const isNegative = amount < 0

  return (
    <span
      className={cn(
        'font-mono tabular-nums',
        size === 'sm' && 'text-sm',
        size === 'md' && 'text-base',
        size === 'lg' && 'text-xl font-semibold',
        showSign && isNegative && 'text-destructive',
        showSign && !isNegative && amount > 0 && 'text-emerald-600 dark:text-emerald-400',
        className,
      )}
    >
      {showSign && isNegative && '−'}
      {showSign && !isNegative && amount > 0 && '+'}
      {formatted}
    </span>
  )
}
