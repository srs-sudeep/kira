import { useState, useRef } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ShieldCheck, ShieldOff, Copy, Eye, EyeOff } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Card, CardContent, CardDescription, CardHeader, CardTitle,
} from '@/components/ui/card'
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from '@/components/ui/form'
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import authService from '@/features/auth/services/auth-service'
import { useAuthStore } from '@/stores/auth-store'

const otpSchema = z.object({
  code: z.string().length(6, 'Enter the 6-digit code'),
})

const disableSchema = z.object({
  code: z.string().length(6, 'Enter your 6-digit code to confirm'),
})

// ── Setup flow (MFA not enabled) ─────────────────────────────────────────────

function MfaSetupFlow({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState<'qr' | 'verify' | 'codes'>('qr')
  const [backupCodes, setBackupCodes] = useState<string[]>([])
  const [showSecret, setShowSecret] = useState(false)

  const { data: setup, isLoading } = useQuery({
    queryKey: ['mfa', 'setup'],
    queryFn: authService.setupMfa,
  })

  const verifyForm = useForm<{ code: string }>({
    resolver: zodResolver(otpSchema),
    defaultValues: { code: '' },
  })

  const verifyMutation = useMutation({
    mutationFn: (code: string) => authService.verifyMfa(code),
    onSuccess(data) {
      setBackupCodes(data.backup_codes ?? [])
      setStep('codes')
    },
  })

  if (isLoading) {
    return <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">Loading setup…</div>
  }

  if (step === 'qr' && setup) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
        </p>
        <div className="flex justify-center">
          <img src={setup.qr_code_uri} alt="MFA QR Code" className="h-40 w-40 rounded-lg border p-2" />
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-muted px-3 py-2">
          <code className="flex-1 text-xs font-mono break-all">
            {showSecret ? setup.secret : '•'.repeat(setup.secret.length)}
          </code>
          <button type="button" onClick={() => setShowSecret((s) => !s)} className="shrink-0">
            {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
          <button
            type="button"
            onClick={() => navigator.clipboard.writeText(setup.secret)}
            className="shrink-0 text-muted-foreground hover:text-foreground"
          >
            <Copy className="h-4 w-4" />
          </button>
        </div>
        <Button onClick={() => setStep('verify')} className="w-full">Next</Button>
      </div>
    )
  }

  if (step === 'verify') {
    return (
      <Form {...verifyForm}>
        <form
          onSubmit={verifyForm.handleSubmit((v) => verifyMutation.mutate(v.code))}
          className="space-y-4"
        >
          <p className="text-sm text-muted-foreground">
            Enter the 6-digit code from your authenticator app to verify setup.
          </p>
          <FormField
            control={verifyForm.control}
            name="code"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Verification Code</FormLabel>
                <FormControl>
                  <Input
                    {...field}
                    inputMode="numeric"
                    maxLength={6}
                    placeholder="000000"
                    className="font-mono text-center text-xl tracking-widest"
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          {verifyMutation.isError && (
            <p className="text-xs text-destructive">Invalid code. Please try again.</p>
          )}
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={() => setStep('qr')}>Back</Button>
            <Button type="submit" className="flex-1" disabled={verifyMutation.isPending}>
              {verifyMutation.isPending ? 'Verifying…' : 'Verify'}
            </Button>
          </div>
        </form>
      </Form>
    )
  }

  // codes step
  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-400 dark:border-amber-900">
        Save these backup codes in a safe place. Each code can be used once if you lose access to your authenticator.
      </div>
      <div className="grid grid-cols-2 gap-2">
        {backupCodes.map((code) => (
          <code key={code} className="rounded bg-muted px-3 py-1.5 text-center text-xs font-mono">
            {code}
          </code>
        ))}
      </div>
      <Button onClick={onDone} className="w-full">Done</Button>
    </div>
  )
}

// ── Disable flow (MFA enabled) ────────────────────────────────────────────────

function MfaDisableFlow({ onDone }: { onDone: () => void }) {
  const form = useForm<{ code: string }>({
    resolver: zodResolver(disableSchema),
    defaultValues: { code: '' },
  })

  const mutation = useMutation({
    mutationFn: (code: string) => authService.disableMfa(code),
    onSuccess: onDone,
  })

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive" size="sm" className="gap-2">
          <ShieldOff className="h-4 w-4" />
          Disable MFA
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Disable two-factor authentication?</AlertDialogTitle>
          <AlertDialogDescription>
            Enter your current authenticator code to confirm. Your account will be less secure without MFA.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit((v) => mutation.mutate(v.code))} className="space-y-4 py-2">
            <FormField
              control={form.control}
              name="code"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Authenticator Code</FormLabel>
                  <FormControl>
                    <Input
                      {...field}
                      inputMode="numeric"
                      maxLength={6}
                      placeholder="000000"
                      className="font-mono text-center text-xl tracking-widest"
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {mutation.isError && (
              <p className="text-xs text-destructive">Invalid code. Please try again.</p>
            )}
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                type="submit"
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                disabled={mutation.isPending}
                onClick={(e) => {
                  // prevent default close; form submit handles it
                  e.preventDefault()
                  form.handleSubmit((v) => mutation.mutate(v.code))()
                }}
              >
                {mutation.isPending ? 'Disabling…' : 'Disable MFA'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </form>
        </Form>
      </AlertDialogContent>
    </AlertDialog>
  )
}

// ── Card ──────────────────────────────────────────────────────────────────────

export function MfaSetupCard() {
  const { user } = useAuthStore()
  const [showSetup, setShowSetup] = useState(false)

  // Track MFA state locally since User type doesn't expose mfa_enabled
  const [mfaEnabled, setMfaEnabled] = useState(false)

  function handleDone() {
    setShowSetup(false)
    setMfaEnabled((prev) => !prev)
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className={`h-5 w-5 ${mfaEnabled ? 'text-accent-600' : 'text-muted-foreground'}`} />
            <CardTitle className="text-base">Two-Factor Authentication</CardTitle>
          </div>
          <Badge variant={mfaEnabled ? 'default' : 'secondary'}>
            {mfaEnabled ? 'Enabled' : 'Disabled'}
          </Badge>
        </div>
        <CardDescription>
          {mfaEnabled
            ? 'Your account is protected with two-factor authentication.'
            : 'Add an extra layer of security with an authenticator app.'}
        </CardDescription>
      </CardHeader>

      <CardContent>
        {mfaEnabled ? (
          <MfaDisableFlow onDone={handleDone} />
        ) : showSetup ? (
          <>
            <Separator className="mb-4" />
            <MfaSetupFlow onDone={handleDone} />
          </>
        ) : (
          <Button size="sm" className="gap-2" onClick={() => setShowSetup(true)}>
            <ShieldCheck className="h-4 w-4" />
            Enable MFA
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
