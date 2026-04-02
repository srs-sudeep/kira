export interface RoomType {
  id: string
  tenant_id: string
  name: string
  code: string
  description?: string
  max_occupancy: number
  base_occupancy: number
  total_rooms: number
  amenities: string[]
  images: string[]
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RatePlan {
  id: string
  room_type_id: string
  name: string
  code: string
  description?: string
  meal_plan: MealPlan
  cancellation_policy: CancellationPolicy
  base_rate: number
  min_los?: number       // minimum length of stay
  max_los?: number
  min_advance_booking?: number  // days
  max_advance_booking?: number  // days
  is_refundable: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export type MealPlan = 'room_only' | 'breakfast' | 'half_board' | 'full_board' | 'all_inclusive'
export type CancellationPolicy = 'free_cancellation' | 'non_refundable' | 'partial_refund'

export interface RoomTypeCreateRequest {
  name: string
  code: string
  description?: string
  max_occupancy: number
  base_occupancy: number
  total_rooms: number
  amenities?: string[]
}

export interface RatePlanCreateRequest {
  room_type_id: string
  name: string
  code: string
  description?: string
  meal_plan: MealPlan
  cancellation_policy: CancellationPolicy
  base_rate: number
  min_los?: number
  max_los?: number
  is_refundable?: boolean
}
