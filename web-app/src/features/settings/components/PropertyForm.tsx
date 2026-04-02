import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Form, FormControl, FormField, FormItem, FormLabel, FormMessage,
} from '@/components/ui/form'
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select'
import type { Tenant, TenantUpdateRequest } from '@/types/tenant'

const STAR_RATINGS = [1, 2, 3, 4, 5] as const

const TIMEZONES = [
  'Asia/Kolkata', 'Asia/Dubai', 'Asia/Singapore', 'Asia/Bangkok',
  'Asia/Tokyo', 'Europe/London', 'Europe/Berlin',
  'America/New_York', 'America/Los_Angeles', 'UTC',
]

const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'AED', 'SGD', 'THB']

const schema = z.object({
  hotel_name: z.string().min(1, 'Hotel name is required'),
  hotel_address: z.string().optional(),
  hotel_city: z.string().optional(),
  hotel_country: z.string().optional(),
  hotel_phone: z.string().optional(),
  hotel_email: z.string().email('Invalid email').optional().or(z.literal('')),
  hotel_website: z.string().url('Invalid URL').optional().or(z.literal('')),
  hotel_star_rating: z.coerce.number().min(1).max(5).optional(),
  timezone: z.string().min(1, 'Timezone is required'),
  currency: z.string().min(3, 'Currency is required'),
})

type FormValues = z.infer<typeof schema>

interface Props {
  tenant?: Tenant
  onSubmit: (values: TenantUpdateRequest) => void
  isSubmitting?: boolean
}

export function PropertyForm({ tenant, onSubmit, isSubmitting }: Props) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      hotel_name: '',
      hotel_address: '',
      hotel_city: '',
      hotel_country: '',
      hotel_phone: '',
      hotel_email: '',
      hotel_website: '',
      hotel_star_rating: 3,
      timezone: 'Asia/Kolkata',
      currency: 'INR',
    },
  })

  useEffect(() => {
    if (tenant) {
      form.reset({
        hotel_name: tenant.hotel_name ?? '',
        hotel_address: tenant.hotel_address ?? '',
        hotel_city: tenant.hotel_city ?? '',
        hotel_country: tenant.hotel_country ?? '',
        hotel_phone: tenant.hotel_phone ?? '',
        hotel_email: tenant.hotel_email ?? '',
        hotel_website: tenant.hotel_website ?? '',
        hotel_star_rating: tenant.hotel_star_rating ?? 3,
        timezone: tenant.timezone ?? 'Asia/Kolkata',
        currency: tenant.currency ?? 'INR',
      })
    }
  }, [tenant, form])

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2">
          <FormField
            control={form.control}
            name="hotel_name"
            render={({ field }) => (
              <FormItem className="sm:col-span-2">
                <FormLabel>Hotel Name</FormLabel>
                <FormControl><Input placeholder="Grand Palace Hotel" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="hotel_address"
            render={({ field }) => (
              <FormItem className="sm:col-span-2">
                <FormLabel>Address</FormLabel>
                <FormControl><Input placeholder="123 Main Street" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="hotel_city"
            render={({ field }) => (
              <FormItem>
                <FormLabel>City</FormLabel>
                <FormControl><Input placeholder="Mumbai" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="hotel_country"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Country</FormLabel>
                <FormControl><Input placeholder="India" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="hotel_phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Phone</FormLabel>
                <FormControl><Input type="tel" placeholder="+91 98765 43210" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="hotel_email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl><Input type="email" placeholder="info@hotel.com" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="hotel_website"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Website</FormLabel>
                <FormControl><Input placeholder="https://hotel.com" {...field} /></FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="hotel_star_rating"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Star Rating</FormLabel>
                <Select
                  value={String(field.value ?? 3)}
                  onValueChange={(v) => field.onChange(Number(v))}
                >
                  <FormControl>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {STAR_RATINGS.map((s) => (
                      <SelectItem key={s} value={String(s)}>
                        {'★'.repeat(s)} {s}-Star
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="timezone"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Timezone</FormLabel>
                <Select value={field.value} onValueChange={field.onChange}>
                  <FormControl>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {TIMEZONES.map((tz) => (
                      <SelectItem key={tz} value={tz}>{tz}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="currency"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Currency</FormLabel>
                <Select value={field.value} onValueChange={field.onChange}>
                  <FormControl>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    {CURRENCIES.map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Save Changes'}
        </Button>
      </form>
    </Form>
  )
}
