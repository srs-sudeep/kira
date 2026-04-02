export interface Notification {
  id: string
  tenant_id: string
  user_id?: string          // null = broadcast to all hotel users
  type: NotificationType
  title: string
  body: string
  data?: Record<string, unknown>
  is_read: boolean
  read_at?: string
  created_at: string
}

export type NotificationType =
  | 'reservation_created'
  | 'reservation_modified'
  | 'reservation_cancelled'
  | 'channel_sync_failed'
  | 'channel_sync_success'
  | 'low_availability'
  | 'rate_update'
  | 'system'

export interface NotificationListParams {
  page?: number
  page_size?: number
  is_read?: boolean
  type?: NotificationType
}

export interface MarkReadRequest {
  notification_ids: string[]
}

export interface NotificationPreferences {
  email_enabled: boolean
  in_app_enabled: boolean
  types: NotificationType[]
}
