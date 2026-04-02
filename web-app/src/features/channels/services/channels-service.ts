import { apiClient } from '@/lib/api-client'
import type { Channel, ChannelMapping, SyncLog, OtaCode } from '@/types/channel'
import type { PaginatedResponse } from '@/types/api'

const BASE = '/api/v1/channels'

export interface ChannelCreatePayload {
  ota: OtaCode
  display_name: string
  hotel_id: string
  api_key: string
  api_secret?: string
}

export interface ChannelUpdatePayload {
  display_name?: string
  hotel_id?: string
  api_key?: string
  api_secret?: string
  is_active?: boolean
}

export interface MappingPayload {
  room_type_id: string
  rate_plan_id: string
  ota_room_id: string
  ota_rate_id: string
  is_active?: boolean
}

export interface SyncLogParams {
  page?: number
  page_size?: number
  status?: 'success' | 'failed' | 'partial'
  sync_type?: 'ari_push' | 'reservation_pull' | 'full_sync'
}

export interface TestConnectionResult {
  success: boolean
  message: string
  hotel_name?: string
}

const channelsService = {
  // ── Channels ─────────────────────────────────────────────────────────────────

  async list(): Promise<Channel[]> {
    const { data } = await apiClient.get<Channel[]>(BASE)
    return data
  },

  async get(id: string): Promise<Channel> {
    const { data } = await apiClient.get<Channel>(`${BASE}/${id}`)
    return data
  },

  async create(payload: ChannelCreatePayload): Promise<Channel> {
    const { data } = await apiClient.post<Channel>(BASE, payload)
    return data
  },

  async update(id: string, payload: ChannelUpdatePayload): Promise<Channel> {
    const { data } = await apiClient.patch<Channel>(`${BASE}/${id}`, payload)
    return data
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`${BASE}/${id}`)
  },

  async testConnection(payload: ChannelCreatePayload): Promise<TestConnectionResult> {
    const { data } = await apiClient.post<TestConnectionResult>(
      `${BASE}/test-connection`,
      payload,
    )
    return data
  },

  async triggerSync(
    id: string,
    syncType: 'ari_push' | 'reservation_pull' | 'full_sync',
    fromDate?: string,
    toDate?: string,
  ): Promise<{ task_id: string }> {
    const { data } = await apiClient.post<{ task_id: string }>(
      `${BASE}/${id}/sync`,
      { sync_type: syncType, from_date: fromDate, to_date: toDate },
    )
    return data
  },

  // ── Mappings ─────────────────────────────────────────────────────────────────

  async listMappings(channelId: string): Promise<ChannelMapping[]> {
    const { data } = await apiClient.get<ChannelMapping[]>(
      `${BASE}/${channelId}/mappings`,
    )
    return data
  },

  async createMapping(channelId: string, payload: MappingPayload): Promise<ChannelMapping> {
    const { data } = await apiClient.post<ChannelMapping>(
      `${BASE}/${channelId}/mappings`,
      payload,
    )
    return data
  },

  async updateMapping(
    channelId: string,
    mappingId: string,
    payload: Partial<MappingPayload>,
  ): Promise<ChannelMapping> {
    const { data } = await apiClient.patch<ChannelMapping>(
      `${BASE}/${channelId}/mappings/${mappingId}`,
      payload,
    )
    return data
  },

  async deleteMapping(channelId: string, mappingId: string): Promise<void> {
    await apiClient.delete(`${BASE}/${channelId}/mappings/${mappingId}`)
  },

  // ── Sync Log ─────────────────────────────────────────────────────────────────

  async getSyncLog(
    channelId: string,
    params?: SyncLogParams,
  ): Promise<PaginatedResponse<SyncLog>> {
    const { data } = await apiClient.get<PaginatedResponse<SyncLog>>(
      `${BASE}/${channelId}/sync-log`,
      { params },
    )
    return data
  },
}

export default channelsService
