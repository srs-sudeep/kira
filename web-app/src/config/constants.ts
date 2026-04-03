// Pagination
export const DEFAULT_PAGE_SIZE = 20
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

// OTA channel identifiers
export const OTA_CHANNELS = {
  BOOKING_COM: 'booking_com',
  EXPEDIA: 'expedia',
  MAKE_MY_TRIP: 'make_my_trip',
} as const

export const OTA_CHANNEL_LABELS: Record<string, string> = {
  booking_com: 'Booking.com',
  expedia: 'Expedia',
  make_my_trip: 'MakeMyTrip',
}

// Reservation statuses
export const RESERVATION_STATUS = {
  CONFIRMED: 'confirmed',
  PENDING: 'pending',
  CANCELLED: 'cancelled',
  NO_SHOW: 'no_show',
  CHECKED_IN: 'checked_in',
  CHECKED_OUT: 'checked_out',
} as const

// Channel sync statuses
export const SYNC_STATUS = {
  SYNCED: 'synced',
  PENDING: 'pending',
  FAILED: 'failed',
  PARTIAL: 'partial',
} as const

// User roles — aligned with identity-service public.users.role CHECK
export const USER_ROLES = {
  SUPER_ADMIN: 'super_admin',
  PROPERTY_OWNER: 'property_owner',
  REVENUE_MANAGER: 'revenue_manager',
  FRONT_DESK: 'front_desk',
  READ_ONLY: 'read_only',
} as const

export type UserRole = (typeof USER_ROLES)[keyof typeof USER_ROLES]

// Date formats
export const DATE_FORMAT = 'yyyy-MM-dd'
export const DISPLAY_DATE_FORMAT = 'dd MMM yyyy'
export const DISPLAY_DATETIME_FORMAT = 'dd MMM yyyy, HH:mm'

// Local storage keys
export const STORAGE_KEYS = {
  AUTH: 'kira-auth',
  UI: 'kira-ui',
} as const

// Query keys factory
export const QUERY_KEYS = {
  AUTH: {
    ME: ['auth', 'me'],
  },
  ROOMS: {
    LIST: (tenantId: string) => ['rooms', tenantId],
    DETAIL: (tenantId: string, id: string) => ['rooms', tenantId, id],
    RATE_PLANS: (roomId: string) => ['rooms', roomId, 'rate-plans'],
  },
  INVENTORY: {
    CALENDAR: (roomId: string, from: string, to: string) => [
      'inventory',
      roomId,
      from,
      to,
    ],
  },
  RESERVATIONS: {
    LIST: (filters?: Record<string, unknown>) => ['reservations', filters],
    DETAIL: (id: string) => ['reservations', id],
  },
  CHANNELS: {
    LIST: (tenantId: string) => ['channels', tenantId],
    DETAIL: (id: string) => ['channels', id],
    SYNC_LOG: (channelId: string) => ['channels', channelId, 'sync-log'],
  },
  NOTIFICATIONS: {
    LIST: (filters?: Record<string, unknown>) => ['notifications', 'list', filters],
    UNREAD_COUNT: ['notifications', 'unread-count'],
    PREFERENCES: ['notifications', 'preferences'],
  },
  SETTINGS: {
    PROPERTY: ['settings', 'property'],
    AUDIT_LOG: (filters?: Record<string, unknown>) => ['settings', 'audit-log', filters],
  },
  USERS: {
    LIST: ['users', 'list'],
    DETAIL: (id: string) => ['users', id],
  },
  TENANTS: {
    LIST: (filters?: Record<string, unknown>) => ['tenants', filters],
    DETAIL: (id: string) => ['tenants', id],
  },
} as const
