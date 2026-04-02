export const ROUTES = {
  // Auth
  LOGIN: '/login',
  MFA_VERIFY: '/mfa-verify',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',

  // App root
  HOME: '/',
  DASHBOARD: '/dashboard',

  // Inventory
  ROOMS: '/rooms',
  ROOM_DETAIL: '/rooms/:roomId',
  RATE_PLANS: '/rooms/:roomId/rate-plans',
  INVENTORY: '/inventory',
  INVENTORY_CALENDAR: '/inventory/calendar',
  SEASONAL_RULES: '/inventory/seasonal-rules',

  // Reservations
  RESERVATIONS: '/reservations',
  RESERVATION_DETAIL: '/reservations/:reservationId',

  // Channels
  CHANNELS: '/channels',
  CHANNEL_DETAIL: '/channels/:channelId',
  CHANNEL_MAPPINGS: '/channels/:channelId/mappings',
  CHANNEL_SYNC_LOG: '/channels/:channelId/sync-log',

  // Notifications
  NOTIFICATIONS: '/notifications',

  // Profile
  PROFILE: '/profile',
  SETTINGS: '/settings',
  SETTINGS_USERS: '/settings/users',
  SETTINGS_AUDIT_LOG: '/settings/audit-log',

  // Admin (super_admin only)
  ADMIN: '/admin',
  ADMIN_TENANTS: '/admin/tenants',
  ADMIN_TENANT_DETAIL: '/admin/tenants/:tenantId',
  ADMIN_USERS: '/admin/users',

  // 404
  NOT_FOUND: '*',
} as const

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES]
