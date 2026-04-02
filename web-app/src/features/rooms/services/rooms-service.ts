import { apiClient } from '@/lib/api-client'
import type { RoomType, RatePlan, RoomTypeCreateRequest, RatePlanCreateRequest } from '@/types/room'
import type { PaginatedResponse } from '@/types/api'

const BASE = '/api/v1/rooms'

const roomsService = {
  // ── Room Types ──────────────────────────────────────────────────────────────

  async listRoomTypes(): Promise<RoomType[]> {
    const { data } = await apiClient.get<RoomType[]>(BASE)
    return data
  },

  async getRoomType(id: string): Promise<RoomType> {
    const { data } = await apiClient.get<RoomType>(`${BASE}/${id}`)
    return data
  },

  async createRoomType(payload: RoomTypeCreateRequest): Promise<RoomType> {
    const { data } = await apiClient.post<RoomType>(BASE, payload)
    return data
  },

  async updateRoomType(
    id: string,
    payload: Partial<RoomTypeCreateRequest> & { is_active?: boolean },
  ): Promise<RoomType> {
    const { data } = await apiClient.patch<RoomType>(`${BASE}/${id}`, payload)
    return data
  },

  async deleteRoomType(id: string): Promise<void> {
    await apiClient.delete(`${BASE}/${id}`)
  },

  // ── Rate Plans ──────────────────────────────────────────────────────────────

  async listRatePlans(roomTypeId: string): Promise<RatePlan[]> {
    const { data } = await apiClient.get<RatePlan[]>(`${BASE}/${roomTypeId}/rate-plans`)
    return data
  },

  async createRatePlan(roomTypeId: string, payload: RatePlanCreateRequest): Promise<RatePlan> {
    const { data } = await apiClient.post<RatePlan>(
      `${BASE}/${roomTypeId}/rate-plans`,
      payload,
    )
    return data
  },

  async updateRatePlan(
    roomTypeId: string,
    planId: string,
    payload: Partial<RatePlanCreateRequest> & { is_active?: boolean },
  ): Promise<RatePlan> {
    const { data } = await apiClient.patch<RatePlan>(
      `${BASE}/${roomTypeId}/rate-plans/${planId}`,
      payload,
    )
    return data
  },

  async deleteRatePlan(roomTypeId: string, planId: string): Promise<void> {
    await apiClient.delete(`${BASE}/${roomTypeId}/rate-plans/${planId}`)
  },
}

export default roomsService
