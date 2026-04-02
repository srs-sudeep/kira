import { apiClient } from '@/lib/api-client'
import type { InventoryDay, BulkUpdateRequest } from '@/types/inventory'

const BASE = '/api/v1/inventory'

export interface CalendarRow {
  room_type_id: string
  room_type_name: string
  rate_plan_id: string
  rate_plan_name: string
  days: InventoryDay[]
}

export interface BlackoutDate {
  id: string
  name: string
  from_date: string
  to_date: string
  affects_all: boolean
  room_type_ids?: string[]
  created_at: string
}

export interface DayUpdatePayload {
  rate?: number
  available_rooms?: number
  stop_sell?: boolean
  is_closed?: boolean
  close_to_arrival?: boolean
  close_to_departure?: boolean
  min_los?: number
  max_los?: number
}

const inventoryService = {
  // ── Calendar ────────────────────────────────────────────────────────────────

  async getCalendar(
    fromDate: string,
    toDate: string,
    roomTypeId?: string,
  ): Promise<CalendarRow[]> {
    const { data } = await apiClient.get<CalendarRow[]>(`${BASE}/calendar`, {
      params: {
        from_date: fromDate,
        to_date: toDate,
        ...(roomTypeId ? { room_type_id: roomTypeId } : {}),
      },
    })
    return data
  },

  // ── Single-day update ────────────────────────────────────────────────────────

  async updateDay(
    roomTypeId: string,
    ratePlanId: string,
    date: string,
    payload: DayUpdatePayload,
  ): Promise<InventoryDay> {
    const { data } = await apiClient.patch<InventoryDay>(
      `${BASE}/${roomTypeId}/${ratePlanId}/${date}`,
      payload,
    )
    return data
  },

  // ── Bulk update ─────────────────────────────────────────────────────────────

  async bulkUpdate(requests: BulkUpdateRequest[]): Promise<void> {
    await apiClient.post(`${BASE}/bulk-update`, { updates: requests })
  },

  // ── Blackout dates ───────────────────────────────────────────────────────────

  async listBlackouts(): Promise<BlackoutDate[]> {
    const { data } = await apiClient.get<BlackoutDate[]>(`${BASE}/blackouts`)
    return data
  },

  async createBlackout(
    payload: Omit<BlackoutDate, 'id' | 'created_at'>,
  ): Promise<BlackoutDate> {
    const { data } = await apiClient.post<BlackoutDate>(`${BASE}/blackouts`, payload)
    return data
  },

  async deleteBlackout(id: string): Promise<void> {
    await apiClient.delete(`${BASE}/blackouts/${id}`)
  },
}

export default inventoryService
