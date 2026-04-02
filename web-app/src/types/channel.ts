export interface Channel {
  id: string
  tenant_id: string
  ota: OtaCode
  display_name: string
  hotel_id: string          // OTA property ID
  api_key?: string          // masked in responses
  is_active: boolean
  sync_status: SyncStatus
  last_synced_at?: string
  last_sync_error?: string
  created_at: string
  updated_at: string
}

export type OtaCode = 'booking_com' | 'expedia' | 'make_my_trip'
export type SyncStatus = 'synced' | 'pending' | 'failed' | 'partial'

export interface ChannelMapping {
  id: string
  channel_id: string
  room_type_id: string
  rate_plan_id: string
  ota_room_id: string
  ota_rate_id: string
  is_active: boolean
}

export interface SyncLog {
  id: string
  channel_id: string
  sync_type: 'ari_push' | 'reservation_pull' | 'full_sync'
  status: 'success' | 'failed' | 'partial'
  records_pushed?: number
  records_pulled?: number
  error_message?: string
  started_at: string
  finished_at?: string
}

export interface ChannelCreateRequest {
  ota: OtaCode
  display_name: string
  hotel_id: string
  api_key: string
  api_secret?: string
}

export interface TriggerSyncRequest {
  sync_type: 'ari_push' | 'reservation_pull' | 'full_sync'
  from_date?: string
  to_date?: string
}
