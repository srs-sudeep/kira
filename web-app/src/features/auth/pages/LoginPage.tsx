import { useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { Hotel, Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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

  // Already logged in → redirect
  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true })
    }
  }, [isAuthenticated, navigate, from])

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const { mutate, isPending, error } = useMutation({
    mutationFn: authService.login,
    onSuccess(data) {
      if (data.mfa_required && data.mfa_token) {
        navigate(ROUTES.MFA_VERIFY, {
          state: { mfa_token: data.mfa_token },
          replace: true,
        })
        return
      }
      if (!data.user) {
        return
      }
      login(data.user, data.access_token, data.refresh_token)
      navigate(from, { replace: true })
    },
  })

  function onSubmit(values: LoginFormValues) {
    mutate(values)
  }

  return (
    <div className="flex min-h-screen">
      {/* Left panel — brand gradient */}
      <div className="hidden lg:flex lg:w-1/2 flex-col items-center justify-center bg-gradient-to-br from-brand-600 to-brand-800 p-12 text-white">
        <div className="max-w-md text-center">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-white/20 backdrop-blur-sm">
            <Hotel className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">KIRA</h1>
          <p className="mt-2 text-lg text-brand-100">Hotel Channel Manager</p>
          <p className="mt-6 text-brand-200 leading-relaxed">
            Distribute your room availability, rates, and inventory across all OTA
            channels from a single dashboard — in real time.
          </p>
          <div className="mt-10 grid grid-cols-3 gap-6 text-center">
            {[
              { value: '3+', label: 'OTA Channels' },
              { value: '99.9%', label: 'Uptime SLA' },
              { value: '<30s', label: 'Sync Speed' },
            ].map(({ value, label }) => (
              <div key={label}>
                <p className="text-2xl font-bold">{value}</p>
                <p className="mt-1 text-xs text-brand-200">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex flex-1 items-center justify-center bg-background p-6">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="mb-8 flex items-center gap-3 lg:hidden">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600">
              <Hotel className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="font-semibold text-foreground">KIRA</p>
              <p className="text-xs text-muted-foreground">Channel Manager</p>
            </div>
          </div>

          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-xl">Sign in</CardTitle>
              <CardDescription>
                Enter your credentials to access your dashboard
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                  <FormField
                    control={form.control}
                    name="email"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Email</FormLabel>
                        <FormControl>
                          <Input
                            type="email"
                            placeholder="you@hotel.com"
                            autoComplete="email"
                            autoFocus
                            {...field}
                          />
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
                          <Link
                            to={ROUTES.FORGOT_PASSWORD}
                            className="text-xs text-brand-600 hover:underline"
                            tabIndex={-1}
                          >
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
                              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                            >
                              {showPassword ? (
                                <EyeOff className="h-4 w-4" />
                              ) : (
                                <Eye className="h-4 w-4" />
                              )}
                            </button>
                          </div>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {/* Server error */}
                  {error && (
                    <p
                      role="alert"
                      className={cn(
                        'rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive',
                      )}
                    >
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
            </CardContent>
          </Card>

          <p className="mt-6 text-center text-xs text-muted-foreground">
            © {new Date().getFullYear()} Abode@AB. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}
