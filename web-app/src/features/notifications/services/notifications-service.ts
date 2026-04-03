import { apiClient } from '@/lib/api-client'
import { ensureArray } from '@/lib/ensure-array'
import type {
  Notification,
  NotificationListParams,
  NotificationPreferences,
  NotificationType,
} from '@/types/notification'
import type { PaginatedResponse } from '@/types/api'

const BASE = '/api/v1/notifications'

const notificationsService = {
  async list(params: NotificationListParams): Promise<PaginatedResponse<Notification>> {
    const { data } = await apiClient.get<PaginatedResponse<Notification>>(BASE, {
      params,
    })
    return data
  },

  async getLatest(limit = 5): Promise<Notification[]> {
    const { data } = await apiClient.get<unknown>(`${BASE}/latest`, {
      params: { limit },
    })
    return ensureArray<Notification>(data)
  },

  async getUnreadCount(): Promise<number> {
    const { data } = await apiClient.get<{ count: number }>(
      `${BASE}/unread-count`,
    )
    return data.count
  },

  async markRead(ids: string[]): Promise<void> {
    await apiClient.post(`${BASE}/mark-read`, { notification_ids: ids })
  },

  async markAllRead(): Promise<void> {
    await apiClient.post(`${BASE}/mark-all-read`)
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`${BASE}/${id}`)
  },

  async bulkDelete(ids: string[]): Promise<void> {
    await apiClient.post(`${BASE}/bulk-delete`, { notification_ids: ids })
  },

  async getPreferences(): Promise<NotificationPreferences> {
    const { data } = await apiClient.get<NotificationPreferences>(
      `${BASE}/preferences`,
    )
    return data
  },

  async updatePreferences(
    payload: Partial<NotificationPreferences>,
  ): Promise<NotificationPreferences> {
    const { data } = await apiClient.patch<NotificationPreferences>(
      `${BASE}/preferences`,
      payload,
    )
    return data
  },
}

export default notificationsService
