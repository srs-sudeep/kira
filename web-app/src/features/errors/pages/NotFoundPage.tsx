import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ROUTES } from '@/router/routes'

export default function NotFoundPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-6">
      {/* Ambient mesh + grid */}
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,hsl(var(--primary)/0.18),transparent)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_100%_100%,hsl(var(--primary)/0.08),transparent)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.35] [background-image:linear-gradient(to_right,hsl(var(--border)/0.5)_1px,transparent_1px),linear-gradient(to_bottom,hsl(var(--border)/0.5)_1px,transparent_1px)] [background-size:48px_48px] dark:opacity-[0.2]"
        aria-hidden
      />

      <div className="relative w-full max-w-md text-center">
        {/* Decorative glow orbs */}
        <div className="absolute -top-24 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full bg-primary/20 blur-3xl" aria-hidden />
        <div className="absolute -bottom-16 -left-8 h-32 w-32 rounded-full bg-accent-500/15 blur-3xl" aria-hidden />
        <div className="absolute -right-10 top-1/3 h-24 w-24 rounded-full bg-primary/10 blur-2xl" aria-hidden />

        {/* Floating ring accent */}
        <div
          className="pointer-events-none absolute left-1/2 top-1/2 h-[120%] w-[120%] -translate-x-1/2 -translate-y-1/2 rounded-[2rem] border border-primary/10 bg-gradient-to-br from-primary/5 via-transparent to-accent-500/5"
          aria-hidden
        />

        <div className="relative rounded-2xl border border-border/40 bg-card/70 p-10 shadow-2xl glass backdrop-blur-xl">
          {/* Inner highlight edge */}
          <div className="pointer-events-none absolute inset-0 rounded-2xl shadow-[inset_0_1px_0_0_hsl(var(--foreground)/0.06)]" aria-hidden />

          <p className="relative text-8xl font-black tracking-tighter bg-gradient-to-br from-primary via-primary/70 to-accent-500 bg-clip-text text-transparent drop-shadow-sm">
            404
          </p>
          <h1 className="relative mt-4 text-xl font-bold text-foreground">Page not found</h1>
          <p className="relative mt-2 text-sm text-muted-foreground/80">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
          <div className="relative mt-8 flex flex-wrap items-center justify-center gap-3">
            <Button
              variant="outline"
              size="sm"
              className="border-border/50 bg-background/40 glass backdrop-blur-md"
              onClick={() => window.history.back()}
            >
              <ArrowLeft className="mr-1.5 h-3.5 w-3.5" />
              Go Back
            </Button>
            <Button size="sm" className="shadow-lg shadow-primary/20" asChild>
              <Link to={ROUTES.DASHBOARD}>
                <Home className="mr-1.5 h-3.5 w-3.5" />
                Dashboard
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
