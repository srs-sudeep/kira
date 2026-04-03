import { useEffect, useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Hotel, Eye, EyeOff, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { useAuthStore } from '@/stores/auth-store'
import { ROUTES } from '@/router/routes'
import authService from '@/features/auth/services/auth-service'
import { getAxiosApiErrorMessage } from '@/lib/api-error'
import { cn } from '@/lib/utils'

const loginSchema = z.object({
  email: z.string().email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
})

type LoginFormValues = z.infer<typeof loginSchema>

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated } = useAuthStore()
  const [showPassword, setShowPassword] = useState(false)

  const from = (location.state as { from?: Location })?.from?.pathname ?? ROUTES.DASHBOARD

  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true })
  }, [isAuthenticated, navigate, from])

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const { mutate, isPending, error } = useMutation({
    mutationFn: authService.login,
    onSuccess(data) {
      if (data.mfa_required && data.mfa_token) {
        navigate(ROUTES.MFA_VERIFY, { state: { mfa_token: data.mfa_token }, replace: true })
        return
      }
      if (!data.user) return
      login(data.user, data.access_token, data.refresh_token)
      navigate(from, { replace: true })
    },
  })

  function onSubmit(values: LoginFormValues) {
    mutate(values)
  }

  return (
    <div className="flex min-h-screen">
      {/* ── Left panel — animated dark gradient ────────────────────────────── */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden">
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950" />

        {/* Animated gradient orbs */}
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-primary/20 blur-[120px] animate-pulse" />
        <div className="absolute -bottom-40 -right-40 h-96 w-96 rounded-full bg-accent-500/20 blur-[120px] animate-pulse [animation-delay:1s]" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-64 w-64 rounded-full bg-violet-500/10 blur-[100px] animate-pulse [animation-delay:2s]" />

        {/* Dot pattern overlay */}
        <div className="absolute inset-0 dot-pattern opacity-20" />

        {/* Floating geometric elements */}
        <div className="absolute top-20 right-20 h-24 w-24 rounded-2xl border border-white/[0.06] bg-white/[0.02] backdrop-blur-sm rotate-12" />
        <div className="absolute bottom-32 left-16 h-16 w-16 rounded-xl border border-white/[0.06] bg-white/[0.02] backdrop-blur-sm -rotate-6" />
        <div className="absolute top-1/3 left-1/4 h-20 w-20 rounded-full border border-white/[0.04] bg-white/[0.01]" />

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center justify-center p-12 text-white w-full">
          <div className="max-w-md text-center">
            <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent-500 shadow-lg shadow-primary/25">
              <Sparkles className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold tracking-tight">KIRA</h1>
            <p className="mt-2 text-lg text-white/60">Hotel Channel Manager</p>
            <p className="mt-6 text-white/40 leading-relaxed">
              Distribute your room availability, rates, and inventory across all OTA
              channels from a single dashboard — in real time.
            </p>
            <div className="mt-10 grid grid-cols-3 gap-6 text-center">
              {[
                { value: '3+', label: 'OTA Channels' },
                { value: '99.9%', label: 'Uptime SLA' },
                { value: '<30s', label: 'Sync Speed' },
              ].map(({ value, label }) => (
                <div key={label} className="rounded-xl border border-white/[0.08] bg-white/[0.03] px-3 py-4 backdrop-blur-sm">
                  <p className="text-2xl font-bold">{value}</p>
                  <p className="mt-1 text-[11px] text-white/40">{label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Right panel — glass login form ─────────────────────────────────── */}
      <div className="flex flex-1 items-center justify-center bg-background p-6 relative">
        {/* Subtle background orb */}
        <div className="absolute top-1/4 right-1/4 h-64 w-64 rounded-full bg-primary/5 blur-[100px]" />

        <div className="relative w-full max-w-sm">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent-500 shadow-lg shadow-primary/20">
              <Hotel className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-foreground">KIRA</p>
              <p className="text-xs text-muted-foreground/60">Channel Manager</p>
            </div>
          </div>

          <div className="rounded-2xl border border-border/40 bg-card/80 glass p-8 shadow-2xl">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-foreground">Sign in</h2>
              <p className="mt-1 text-sm text-muted-foreground/70">Enter your credentials to access your dashboard</p>
            </div>

            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input type="email" placeholder="you@hotel.com" autoComplete="email" autoFocus {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel>Password</FormLabel>
                        <Link to={ROUTES.FORGOT_PASSWORD} className="text-xs text-primary hover:underline" tabIndex={-1}>
                          Forgot password?
                        </Link>
                      </div>
                      <FormControl>
                        <div className="relative">
                          <Input
                            type={showPassword ? 'text' : 'password'}
                            placeholder="••••••••"
                            autoComplete="current-password"
                            className="pr-10"
                            {...field}
                          />
                          <button
                            type="button"
                            tabIndex={-1}
                            onClick={() => setShowPassword((p) => !p)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-foreground transition-colors"
                          >
                            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                          </button>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {error && (
                  <p role="alert" className={cn('rounded-xl bg-destructive/10 px-3 py-2 text-sm text-destructive')}>
                    {getAxiosApiErrorMessage(error, 'Invalid email or password')}
                  </p>
                )}

                <Button type="submit" className="w-full" disabled={isPending}>
                  {isPending ? (
                    <span className="flex items-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                      Signing in…
                    </span>
                  ) : (
                    'Sign in'
                  )}
                </Button>
              </form>
            </Form>
          </div>

          <p className="mt-6 text-center text-xs text-muted-foreground/50">
            © {new Date().getFullYear()} Abode@AB. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}
