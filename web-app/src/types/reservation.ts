export interface Reservation {
  id: string
  tenant_id: string
  booking_reference: string
  channel: string
  channel_booking_id: string
  room_type_id: string
  room_type_name: string
  rate_plan_id: string
  rate_plan_name: string
  guest: Guest
  check_in_date: string
  check_out_date: string
  nights: number
  adults: number
  children: number
  total_amount: number
  currency: string
  status: ReservationStatus
  special_requests?: string
  cancellation_reason?: string
  cancelled_at?: string
  created_at: string
  updated_at: string
}

export interface Guest {
  first_name: string
  last_name: string
  email: string
  phone?: string
  country?: string
  id_type?: string
  id_number?: string
}

export type ReservationStatus =
  | 'confirmed'
  | 'pending'
  | 'cancelled'
  | 'no_show'
  | 'checked_in'
  | 'checked_out'

export interface ReservationListParams {
  page?: number
  page_size?: number
  status?: ReservationStatus
  channel?: string
  check_in_from?: string
  check_in_to?: string
  search?: string
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
}

export interface ModifyReservationRequest {
  check_in_date?: string
  check_out_date?: string
  adults?: number
  children?: number
  room_type_id?: string
  rate_plan_id?: string
  special_requests?: string
}

export interface CancelReservationRequest {
  reason: string
}
