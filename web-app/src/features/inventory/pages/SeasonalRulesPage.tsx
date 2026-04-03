import { Calendar } from 'lucide-react'
import { PageHeader } from '@/components/shared/PageHeader'

export default function SeasonalRulesPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        title="Seasonal Rules"
        description="Define pricing adjustments for peak and off-peak seasons."
      />

      <div className="relative overflow-hidden rounded-2xl border border-border/40 bg-card/50 p-10 shadow-xl glass backdrop-blur-xl">
        <div
          className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-primary/15 blur-3xl"
          aria-hidden
        />
        <div
          className="pointer-events-none absolute -bottom-12 -left-12 h-32 w-32 rounded-full bg-accent-500/10 blur-3xl"
          aria-hidden
        />

        <div className="relative flex flex-col items-center justify-center py-6 text-center">
          <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent-500 shadow-lg shadow-primary/25">
            <Calendar className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-lg font-semibold tracking-tight text-foreground">
            Seasonal rules coming soon
          </h2>
          <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground/80">
            Automatically adjust rates based on demand patterns once seasonal rule authoring is
            available.
          </p>
        </div>
      </div>
    </div>
  )
}
