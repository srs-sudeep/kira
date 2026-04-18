import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from '@/components/ui/dialog'
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from '@/components/ui/form'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import type { InviteUserPayload } from '../services/users-service'

const schema = z.object({
  full_name: z.string().min(2, 'Full name is required'),
  email: z.string().email('Invalid email'),
  role: z.enum(['property_owner', 'revenue_manager', 'front_desk', 'read_only'], {
    required_error: 'Role is required',
  }),
})

const ROLE_LABELS: Record<string, string> = {
  property_owner: 'Property owner',
  revenue_manager: 'Revenue manager',
  front_desk: 'Front desk',
  read_only: 'Read only',
}

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (payload: InviteUserPayload) => void
  isSubmitting?: boolean
}

export function InviteUserDialog({ open, onOpenChange, onSubmit, isSubmitting }: Props) {
  const form = useForm<InviteUserPayload>({
    resolver: zodResolver(schema),
    defaultValues: { full_name: '', email: '', role: 'front_desk' },
  })

  function handleSubmit(values: InviteUserPayload) {
    onSubmit(values)
  }

  function handleOpenChange(o: boolean) {
    if (!o) form.reset()
    onOpenChange(o)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invite User</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Full Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Jane Smith" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="jane@hotel.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {Object.entries(ROLE_LABELS).map(([value, label]) => (
                        <SelectItem key={value} value={value}>{label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Sending…' : 'Send Invite'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
