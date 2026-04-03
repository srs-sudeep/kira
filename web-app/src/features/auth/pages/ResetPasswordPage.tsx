import { Link } from 'react-router-dom'
import { KeyRound, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ROUTES } from '@/router/routes'

export default function ResetPasswordPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-6 dot-pattern">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,hsl(var(--primary)/0.18),transparent)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_100%_100%,hsl(var(--primary)/0.08),transparent)]"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -top-24 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full bg-primary/20 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -bottom-16 -left-8 h-32 w-32 rounded-full bg-accent-500/15 blur-3xl"
        aria-hidden
      />
      <div
        className="pointer-events-none absolute -right-10 top-1/3 h-24 w-24 rounded-full bg-primary/10 blur-2xl"
        aria-hidden
      />

      <div className="relative w-full max-w-sm">
        <div className="rounded-2xl border border-border/40 bg-card/70 p-8 shadow-2xl glass backdrop-blur-xl">
          <div className="mb-6 flex flex-col items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent-500 shadow-lg shadow-primary/20">
              <KeyRound className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl font-bold">Set new password</h1>
            <p className="text-center text-sm text-muted-foreground/70">
              Choose a strong password for your account.
            </p>
          </div>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label>New password</Label>
              <Input
                type="password"
                placeholder="••••••••"
                className="rounded-xl border-border/40 bg-muted/30 focus-visible:ring-primary/20"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Confirm password</Label>
              <Input
                type="password"
                placeholder="••••••••"
                className="rounded-xl border-border/40 bg-muted/30 focus-visible:ring-primary/20"
              />
            </div>
            <Button className="w-full shadow-lg shadow-primary/15" disabled>
              Update password
            </Button>
            <p className="text-center text-xs text-muted-foreground/50">This feature is coming soon.</p>
          </div>
          <div className="mt-6 text-center">
            <Link
              to={ROUTES.LOGIN}
              className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
