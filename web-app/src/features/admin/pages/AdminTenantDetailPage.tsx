import { Building2 } from 'lucide-react'
import { PageHeader } from '@/components/shared/PageHeader'

export default function AdminTenantDetailPage() {
  return (
    <div className="space-y-8">
      <PageHeader title="Tenant Details" description="View and manage tenant configuration." />

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
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <h2 className="text-lg font-semibold tracking-tight text-foreground">
            Tenant details coming soon
          </h2>
          <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground/80">
            Per-tenant settings, billing, and audit history will appear here as the admin experience
            is built out.
          </p>
        </div>
      </div>
    </div>
  )
}
