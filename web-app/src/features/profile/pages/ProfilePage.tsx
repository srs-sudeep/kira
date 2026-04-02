import { useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Camera } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from '@/components/ui/form'
import { QUERY_KEYS } from '@/config/constants'
import { getInitials } from '@/lib/utils'
import { useAuthStore } from '@/stores/auth-store'
import authService from '@/features/auth/services/auth-service'
import { MfaSetupCard } from '@/features/settings/components/MfaSetupCard'

// ── Personal info form ────────────────────────────────────────────────────────

const infoSchema = z.object({
  full_name: z.string().min(2, 'Full name is required'),
  email: z.string().email('Invalid email'),
})

// ── Change password form ──────────────────────────────────────────────────────

const passwordSchema = z
  .object({
    current_password: z.string().min(1, 'Required'),
    new_password: z
      .string()
      .min(8, 'Minimum 8 characters')
      .regex(/[A-Z]/, 'Must contain uppercase')
      .regex(/[0-9]/, 'Must contain a number'),
    confirm_password: z.string(),
  })
  .refine((d) => d.new_password === d.confirm_password, {
    message: 'Passwords do not match',
    path: ['confirm_password'],
  })

type PasswordValues = z.infer<typeof passwordSchema>

function ChangePasswordForm() {
  const form = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: '', new_password: '', confirm_password: '' },
  })

  const mutation = useMutation({
    mutationFn: (v: PasswordValues) =>
      authService.changePassword({ current_password: v.current_password, new_password: v.new_password }),
    onSuccess() {
      form.reset()
    },
  })

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
        <FormField
          control={form.control}
          name="current_password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Current Password</FormLabel>
              <FormControl><Input type="password" {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="new_password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>New Password</FormLabel>
              <FormControl><Input type="password" {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="confirm_password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Confirm New Password</FormLabel>
              <FormControl><Input type="password" {...field} /></FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        {mutation.isError && (
          <p className="text-xs text-destructive">
            Failed to change password. Check your current password.
          </p>
        )}
        {mutation.isSuccess && (
          <p className="text-xs text-accent-600">Password changed successfully.</p>
        )}
        <Button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? 'Updating…' : 'Update Password'}
        </Button>
      </form>
    </Form>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ProfilePage() {
  const qc = useQueryClient()
  const { user } = useAuthStore()
  const fileRef = useRef<HTMLInputElement>(null)

  const { data: me } = useQuery({
    queryKey: QUERY_KEYS.AUTH.ME,
    queryFn: authService.getMe,
    initialData: user ?? undefined,
  })

  const infoForm = useForm({
    resolver: zodResolver(infoSchema),
    values: me ? { full_name: me.full_name, email: me.email } : undefined,
  })

  const { updateUser } = useAuthStore()

  const updateMeMutation = useMutation({
    mutationFn: (values: { full_name: string; email: string }) =>
      authService.updateMe({ full_name: values.full_name }),
    onSuccess(data) {
      updateUser(data)
      qc.invalidateQueries({ queryKey: QUERY_KEYS.AUTH.ME })
    },
  })

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Profile</h1>
        <p className="text-sm text-muted-foreground">Manage your personal information and security</p>
      </div>

      <div className="grid max-w-2xl gap-6">
        {/* Personal info */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Personal Information</CardTitle>
            <CardDescription>Update your name and email address</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {/* Avatar */}
            <div className="flex items-center gap-4">
              <div className="relative">
                <Avatar className="h-16 w-16">
                  <AvatarImage src={me?.avatar_url} alt={me?.full_name} />
                  <AvatarFallback className="text-lg">
                    {me ? getInitials(me.full_name) : 'U'}
                  </AvatarFallback>
                </Avatar>
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  className="absolute bottom-0 right-0 flex h-6 w-6 items-center justify-center rounded-full bg-brand-600 text-white shadow hover:bg-brand-700"
                  aria-label="Change avatar"
                >
                  <Camera className="h-3 w-3" />
                </button>
                <input ref={fileRef} type="file" accept="image/*" className="hidden" />
              </div>
              <div>
                <p className="font-semibold">{me?.full_name}</p>
                <p className="text-sm text-muted-foreground">{me?.email}</p>
              </div>
            </div>

            <Separator />

            <Form {...infoForm}>
              <form
                onSubmit={infoForm.handleSubmit((v) => updateMeMutation.mutate(v))}
                className="space-y-4"
              >
                <FormField
                  control={infoForm.control}
                  name="full_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Full Name</FormLabel>
                      <FormControl><Input {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={infoForm.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl><Input type="email" {...field} /></FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button type="submit" disabled={updateMeMutation.isPending}>
                  {updateMeMutation.isPending ? 'Saving…' : 'Save Changes'}
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Change password */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Change Password</CardTitle>
            <CardDescription>Use a strong password you don't use elsewhere</CardDescription>
          </CardHeader>
          <CardContent>
            <ChangePasswordForm />
          </CardContent>
        </Card>

        {/* MFA */}
        <MfaSetupCard />
      </div>
    </div>
  )
}
