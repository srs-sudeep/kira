import {
  useRef,
  useState,
  useCallback,
  type ClipboardEvent,
  type KeyboardEvent,
  type ChangeEvent,
} from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Hotel, ShieldCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/stores/auth-store'
import { ROUTES } from '@/router/routes'
import authService from '@/features/auth/services/auth-service'
import { cn } from '@/lib/utils'

const OTP_LENGTH = 6

export default function MfaVerifyPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuthStore()

  const mfaToken = (location.state as { mfa_token?: string } | null)?.mfa_token

  // Redirect back to login if no token in state
  if (!mfaToken) {
    navigate(ROUTES.LOGIN, { replace: true })
    return null
  }

  const [digits, setDigits] = useState<string[]>(Array(OTP_LENGTH).fill(''))
  const inputRefs = useRef<Array<HTMLInputElement | null>>(Array(OTP_LENGTH).fill(null))

  const { mutate, isPending, error, reset } = useMutation({
    mutationFn: (totp_code: string) =>
      authService.mfaLogin({ mfa_token: mfaToken, totp_code }),
    onSuccess(data) {
      if (!data.user) return
      login(data.user, data.access_token, data.refresh_token)
      navigate(ROUTES.DASHBOARD, { replace: true })
    },
    onError() {
      // Clear inputs on wrong code
      setDigits(Array(OTP_LENGTH).fill(''))
      inputRefs.current[0]?.focus()
    },
  })

  const submitOtp = useCallback(
    (code: string) => {
      if (code.length === OTP_LENGTH) {
        mutate(code)
      }
    },
    [mutate],
  )

  function handleChange(index: number, e: ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value.replace(/\D/g, '')
    if (!raw) return

    const newDigits = [...digits]

    // Handle paste-like multi-char input into a cell
    if (raw.length > 1) {
      const chars = raw.slice(0, OTP_LENGTH - index).split('')
      chars.forEach((ch, i) => {
        if (index + i < OTP_LENGTH) newDigits[index + i] = ch
      })
      setDigits(newDigits)
      const nextFocus = Math.min(index + chars.length, OTP_LENGTH - 1)
      inputRefs.current[nextFocus]?.focus()
      const joined = newDigits.join('')
      if (joined.length === OTP_LENGTH) submitOtp(joined)
      return
    }

    newDigits[index] = raw
    setDigits(newDigits)
    reset()

    if (index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus()
    }

    const joined = newDigits.join('')
    if (joined.length === OTP_LENGTH) submitOtp(joined)
  }

  function handleKeyDown(index: number, e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Backspace') {
      if (digits[index]) {
        const newDigits = [...digits]
        newDigits[index] = ''
        setDigits(newDigits)
        reset()
      } else if (index > 0) {
        inputRefs.current[index - 1]?.focus()
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === 'ArrowRight' && index < OTP_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  function handlePaste(e: ClipboardEvent<HTMLInputElement>) {
    e.preventDefault()
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, OTP_LENGTH)
    if (!pasted) return
    const newDigits = Array(OTP_LENGTH)
      .fill('')
      .map((_, i) => pasted[i] ?? '')
    setDigits(newDigits)
    reset()
    const nextFocus = Math.min(pasted.length, OTP_LENGTH - 1)
    inputRefs.current[nextFocus]?.focus()
    if (pasted.length === OTP_LENGTH) submitOtp(pasted)
  }

  function handleManualSubmit() {
    submitOtp(digits.join(''))
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-600">
            <Hotel className="h-6 w-6 text-white" />
          </div>
          <div className="text-center">
            <p className="font-semibold text-foreground">KIRA</p>
            <p className="text-xs text-muted-foreground">Channel Manager</p>
          </div>
        </div>

        <Card>
          <CardHeader className="pb-4 text-center">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-brand-50 dark:bg-brand-950">
              <ShieldCheck className="h-5 w-5 text-brand-600" />
            </div>
            <CardTitle className="text-xl">Two-factor authentication</CardTitle>
            <CardDescription>
              Enter the 6-digit code from your authenticator app
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-6">
            {/* OTP input grid */}
            <div className="flex justify-center gap-2">
              {digits.map((digit, i) => (
                <input
                  key={i}
                  ref={(el) => {
                    inputRefs.current[i] = el
                  }}
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={6}
                  value={digit}
                  autoFocus={i === 0}
                  disabled={isPending}
                  onChange={(e) => handleChange(i, e)}
                  onKeyDown={(e) => handleKeyDown(i, e)}
                  onPaste={handlePaste}
                  onFocus={(e) => e.target.select()}
                  aria-label={`Digit ${i + 1}`}
                  className={cn(
                    'h-12 w-10 rounded-md border bg-background text-center text-lg font-semibold',
                    'outline-none ring-offset-background transition-colors',
                    'focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30',
                    error
                      ? 'border-destructive text-destructive'
                      : 'border-input text-foreground',
                    isPending && 'opacity-50',
                  )}
                />
              ))}
            </div>

            {/* Error */}
            {error && (
              <p role="alert" className="text-center text-sm text-destructive">
                Invalid code. Please check your authenticator app and try again.
              </p>
            )}

            <Button
              className="w-full"
              onClick={handleManualSubmit}
              disabled={isPending || digits.join('').length < OTP_LENGTH}
            >
              {isPending ? (
                <span className="flex items-center gap-2">
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Verifying…
                </span>
              ) : (
                'Verify'
              )}
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              Wrong account?{' '}
              <button
                type="button"
                onClick={() => navigate(ROUTES.LOGIN)}
                className="text-brand-600 hover:underline"
              >
                Back to sign in
              </button>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
