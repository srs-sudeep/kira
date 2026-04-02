export interface Tenant {
  id: string
  name: string
  slug: string
  schema_name: string
  subscription_plan: SubscriptionPlan
  subscription_status: SubscriptionStatus
  hotel_name: string
  hotel_address?: string
  hotel_city?: string
  hotel_country?: string
  hotel_phone?: string
  hotel_email?: string
  hotel_website?: string
  hotel_star_rating?: 1 | 2 | 3 | 4 | 5
  timezone: string
  currency: string
  logo_url?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type SubscriptionPlan = 'starter' | 'professional' | 'enterprise'
export type SubscriptionStatus = 'active' | 'trialing' | 'past_due' | 'cancelled' | 'suspended'

export interface TenantCreateRequest {
  name: string
  hotel_name: string
  admin_email: string
  admin_full_name: string
  subscription_plan: SubscriptionPlan
  timezone?: string
  currency?: string
}

export interface TenantUpdateRequest {
  name?: string
  hotel_name?: string
  hotel_address?: string
  hotel_city?: string
  hotel_country?: string
  hotel_phone?: string
  hotel_email?: string
  hotel_website?: string
  hotel_star_rating?: 1 | 2 | 3 | 4 | 5
  timezone?: string
  currency?: string
}
