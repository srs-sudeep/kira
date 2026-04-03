import { apiClient } from '@/lib/api-client'
import { ensureArray } from '@/lib/ensure-array'
import type { Reservation, ReservationListParams, ModifyReservationRequest } from '@/types/reservation'
import type { PaginatedResponse } from '@/types/api'
import type { Guest } from '@/types/reservation'

const BASE = '/api/v1/reservations'

export interface ReservationNote {
  id: string
  reservation_id: string
  author_name: string
  author_id: string
  body: string
  created_at: string
}

export interface CreateReservationPayload {
  room_type_id: string
  rate_plan_id: string
  check_in_date: string
  check_out_date: string
  adults: number
  children: number
  guest: Guest
  special_requests?: string
}

const reservationsService = {
  // ── Reservations ─────────────────────────────────────────────────────────────

  async list(params: ReservationListParams): Promise<PaginatedResponse<Reservation>> {
    const { data } = await apiClient.get<PaginatedResponse<Reservation>>(BASE, { params })
    return data
  },

  async get(id: string): Promise<Reservation> {
    const { data } = await apiClient.get<Reservation>(`${BASE}/${id}`)
    return data
  },

  async create(payload: CreateReservationPayload): Promise<Reservation> {
    const { data } = await apiClient.post<Reservation>(BASE, payload)
    return data
  },

  async update(id: string, payload: ModifyReservationRequest): Promise<Reservation> {
    const { data } = await apiClient.patch<Reservation>(`${BASE}/${id}`, payload)
    return data
  },

  async cancel(id: string, reason: string): Promise<Reservation> {
    const { data } = await apiClient.post<Reservation>(`${BASE}/${id}/cancel`, { reason })
    return data
  },

  async checkIn(id: string): Promise<Reservation> {
    const { data } = await apiClient.post<Reservation>(`${BASE}/${id}/check-in`)
    return data
  },

  async checkOut(id: string): Promise<Reservation> {
    const { data } = await apiClient.post<Reservation>(`${BASE}/${id}/check-out`)
    return data
  },

  async markNoShow(id: string): Promise<Reservation> {
    const { data } = await apiClient.post<Reservation>(`${BASE}/${id}/no-show`)
    return data
  },

  // ── Notes ────────────────────────────────────────────────────────────────────

  async listNotes(reservationId: string): Promise<ReservationNote[]> {
    const { data } = await apiClient.get<unknown>(`${BASE}/${reservationId}/notes`)
    return ensureArray<ReservationNote>(data)
  },

  async addNote(reservationId: string, body: string): Promise<ReservationNote> {
    const { data } = await apiClient.post<ReservationNote>(
      `${BASE}/${reservationId}/notes`,
      { body },
    )
    return data
  },

  async deleteNote(reservationId: string, noteId: string): Promise<void> {
    await apiClient.delete(`${BASE}/${reservationId}/notes/${noteId}`)
  },
}

export default reservationsService
