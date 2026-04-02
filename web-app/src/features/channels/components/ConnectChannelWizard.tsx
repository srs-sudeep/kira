import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  CheckCircle2,
  XCircle,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import { ROUTES } from '@/router/routes'
import channelsService from '../services/channels-service'
import type { OtaCode } from '@/types/channel'

const OTAS: { code: OtaCode; name: string; description: string; gradient: string; initial: string }[] = [
  {
    code: 'booking_com',
    name: 'Booking.com',
    description: "World's largest accommodation platform",
    gradient: 'from-blue-500 to-blue-700',
    initial: 'B.',
  },
  {
    code: 'expedia',
    name: 'Expedia',
    description: 'Global travel marketplace',
    gradient: 'from-yellow-400 to-orange-500',
    initial: 'EX',
  },
  {
    code: 'make_my_trip',
    name: 'MakeMyTrip',
    description: "India's leading travel company",
    gradient: 'from-red-500 to-red-700',
    initial: 'MMT',
  },
]

type Step = 'select' | 'credentials' | 'test'

interface WizardState {
  ota: OtaCode | null
  display_name: string
  hotel_id: string
  api_key: string
  api_secret: string
}

export function ConnectChannelWizard() {
  const navigate = useNavigate()
  const [step, setStep] = useState<Step>('select')
  const [showKey, setShowKey] = useState(false)
  const [testResult, setTestResult] = useState<{
    success: boolean
    message: string
    hotel_name?: string
  } | null>(null)

  const [state, setState] = useState<WizardState>({
    ota: null,
    display_name: '',
    hotel_id: '',
    api_key: '',
    api_secret: '',
  })

  function set(patch: Partial<WizardState>) {
    setState((p) => ({ ...p, ...patch }))
  }

  // Pre-fill display name when OTA selected
  function selectOta(code: OtaCode) {
    const ota = OTAS.find((o) => o.code === code)!
    set({ ota: code, display_name: ota.name })
    setStep('credentials')
  }

  const testMutation = useMutation({
    mutationFn: () =>
      channelsService.testConnection({
        ota: state.ota!,
        display_name: state.display_name,
        hotel_id: state.hotel_id,
        api_key: state.api_key,
        api_secret: state.api_secret || undefined,
      }),
    onSuccess(data) {
      setTestResult(data)
    },
    onError() {
      setTestResult({ success: false, message: 'Connection test failed. Check your credentials.' })
    },
  })

  const createMutation = useMutation({
    mutationFn: () =>
      channelsService.create({
        ota: state.ota!,
        display_name: state.display_name,
        hotel_id: state.hotel_id,
        api_key: state.api_key,
        api_secret: state.api_secret || undefined,
      }),
    onSuccess(channel) {
      toast.success(`${channel.display_name} connected successfully!`)
      navigate(ROUTES.CHANNEL_DETAIL.replace(':channelId', channel.id))
    },
  })

  const credentialsValid =
    state.display_name.trim() && state.hotel_id.trim() && state.api_key.trim()

  const STEPS: Record<Step, number> = { select: 0, credentials: 1, test: 2 }
  const STEP_LABELS = ['Choose OTA', 'Credentials', 'Test & Connect']

  return (
    <div className="mx-auto max-w-xl space-y-6">
      {/* Step indicator */}
      <div className="flex items-center justify-center gap-3">
        {STEP_LABELS.map((label, i) => {
          const currentIdx = STEPS[step]
          return (
            <div key={label} className="flex items-center gap-2">
              <div
                className={cn(
                  'flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold',
                  i < currentIdx
                    ? 'bg-brand-600 text-white'
                    : i === currentIdx
                      ? 'bg-brand-100 text-brand-700 ring-2 ring-brand-600'
                      : 'bg-muted text-muted-foreground',
                )}
              >
                {i < currentIdx ? <CheckCircle2 className="h-4 w-4" /> : i + 1}
              </div>
              <span
                className={cn(
                  'text-sm',
                  i === currentIdx ? 'font-medium text-foreground' : 'text-muted-foreground',
                )}
              >
                {label}
              </span>
              {i < STEP_LABELS.length - 1 && (
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
              )}
            </div>
          )
        })}
      </div>

      <Separator />

      {/* ── Step 1: Select OTA ─────────────────────────────────────────────── */}
      {step === 'select' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Choose a channel</h2>
            <p className="text-sm text-muted-foreground">Select the OTA you want to connect.</p>
          </div>
          <div className="space-y-3">
            {OTAS.map((ota) => (
              <button
                key={ota.code}
                type="button"
                onClick={() => selectOta(ota.code)}
                className="group flex w-full items-center gap-4 rounded-xl border p-4 text-left transition-all hover:border-brand-400 hover:shadow-sm"
              >
                <div
                  className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${ota.gradient}`}
                >
                  <span className="text-sm font-bold text-white">{ota.initial}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-foreground">{ota.name}</p>
                  <p className="text-sm text-muted-foreground">{ota.description}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Step 2: Credentials ────────────────────────────────────────────── */}
      {step === 'credentials' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Enter credentials</h2>
            <p className="text-sm text-muted-foreground">
              These are provided by {OTAS.find((o) => o.code === state.ota)?.name} in your
              extranet / partner portal.
            </p>
          </div>

          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label>Display Name</Label>
              <Input
                value={state.display_name}
                onChange={(e) => set({ display_name: e.target.value })}
                placeholder="e.g. Booking.com — Main Property"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Hotel / Property ID</Label>
              <Input
                value={state.hotel_id}
                onChange={(e) => set({ hotel_id: e.target.value })}
                placeholder="Your OTA property ID"
              />
            </div>
            <div className="space-y-1.5">
              <Label>API Key</Label>
              <div className="relative">
                <Input
                  type={showKey ? 'text' : 'password'}
                  value={state.api_key}
                  onChange={(e) => set({ api_key: e.target.value })}
                  placeholder="••••••••••••"
                  className="pr-10"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  onClick={() => setShowKey((p) => !p)}
                >
                  {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>
                API Secret{' '}
                <span className="text-xs text-muted-foreground">(if required)</span>
              </Label>
              <Input
                type="password"
                value={state.api_secret}
                onChange={(e) => set({ api_secret: e.target.value })}
                placeholder="Optional secret key"
              />
            </div>
          </div>

          <div className="flex justify-between pt-2">
            <Button variant="ghost" onClick={() => setStep('select')}>
              <ChevronLeft className="mr-1 h-4 w-4" /> Back
            </Button>
            <Button
              disabled={!credentialsValid}
              onClick={() => {
                setTestResult(null)
                setStep('test')
              }}
            >
              Next <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* ── Step 3: Test & Connect ─────────────────────────────────────────── */}
      {step === 'test' && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Test connection</h2>
            <p className="text-sm text-muted-foreground">
              Verify your credentials before saving.
            </p>
          </div>

          {/* Summary */}
          <div className="rounded-lg border bg-muted/30 p-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">OTA</span>
              <span className="font-medium">{OTAS.find((o) => o.code === state.ota)?.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Display Name</span>
              <span className="font-medium">{state.display_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Hotel ID</span>
              <span className="font-mono font-medium">{state.hotel_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">API Key</span>
              <span className="font-mono text-muted-foreground">
                {'•'.repeat(Math.min(state.api_key.length, 8))}
              </span>
            </div>
          </div>

          {/* Test result */}
          {testResult && (
            <div
              className={cn(
                'flex items-start gap-3 rounded-lg p-4',
                testResult.success
                  ? 'bg-accent-50 dark:bg-accent-950/30'
                  : 'bg-destructive/10',
              )}
            >
              {testResult.success ? (
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-accent-600" />
              ) : (
                <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
              )}
              <div>
                <p
                  className={cn(
                    'font-medium text-sm',
                    testResult.success ? 'text-accent-700' : 'text-destructive',
                  )}
                >
                  {testResult.success ? 'Connection successful' : 'Connection failed'}
                </p>
                {testResult.hotel_name && (
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Property: {testResult.hotel_name}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-0.5">{testResult.message}</p>
              </div>
            </div>
          )}

          <div className="flex justify-between pt-2">
            <Button variant="ghost" onClick={() => { setStep('credentials'); setTestResult(null) }}>
              <ChevronLeft className="mr-1 h-4 w-4" /> Back
            </Button>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => testMutation.mutate()}
                disabled={testMutation.isPending}
              >
                {testMutation.isPending ? (
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                ) : null}
                Test Connection
              </Button>
              <Button
                onClick={() => createMutation.mutate()}
                disabled={!testResult?.success || createMutation.isPending}
              >
                {createMutation.isPending ? 'Connecting…' : 'Connect Channel'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
