export interface InventoryDay {
  date: string           // YYYY-MM-DD
  room_type_id: string
  rate_plan_id: string
  available_rooms: number
  total_rooms: number
  rate: number
  is_closed: boolean
  min_los?: number
  max_los?: number
  stop_sell: boolean
  close_to_arrival: boolean
  close_to_departure: boolean
}

export interface InventoryCalendarResponse {
  room_type_id: string
  rate_plan_id: string
  from_date: string
  to_date: string
  days: InventoryDay[]
}

export interface BulkUpdateRequest {
  room_type_id: string
  rate_plan_id: string
  from_date: string
  to_date: string
  days_of_week?: number[]   // 0=Mon … 6=Sun; empty = all days
  available_rooms?: number
  rate?: number
  is_closed?: boolean
  stop_sell?: boolean
  close_to_arrival?: boolean
  close_to_departure?: boolean
  min_los?: number
  max_los?: number
}

export interface SeasonalRule {
  id: string
  name: string
  room_type_id: string
  rate_plan_id: string
  from_date: string
  to_date: string
  rate_multiplier: number   // e.g. 1.2 = 20% premium
  min_los?: number
  is_active: boolean
  created_at: string
}
