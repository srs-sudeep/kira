import { apiClient } from '@/lib/api-client'
import type { Reservation } from '@/types/reservation'
import type { SyncStatus } from '@/types/channel'

/** Coerce unknown API payloads to T[] so charts/lists never receive a plain object. */
function ensureArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value
  if (value && typeof value === 'object' && 'items' in value) {
    const items = (value as { items: unknown }).items
    if (Array.isArray(items)) return items as T[]
  }
  return []
}

// ── Response shapes ──────────────────────────────────────────────────────────

export interface KpiSummary {
  total_reservations: number
  reservations_change_pct: number   // e.g. 12.5 = +12.5 %
  total_revenue: number
  revenue_change_pct: number
  occupancy_rate: number             // 0–100
  occupancy_change_pct: number
  cancellation_rate: number          // 0–100
  cancellation_change_pct: number
  period_label: string               // e.g. "vs last 30 days"
}

export interface TodaySnapshot {
  arrivals: number
  departures: number
  stay_overs: number
  no_shows: number
  total_occupied: number
  total_rooms: number
  occupancy_pct: number
}

export interface OccupancyDataPoint {
  date: string         // YYYY-MM-DD
  occupancy_pct: number
  occupied_rooms: number
  available_rooms: number
}

export interface BookingSource {
  channel: string
  display_name: string
  count: number
  percentage: number
  revenue: number
}

export interface ChannelHealthItem {
  channel_id: string
  ota: string
  display_name: string
  sync_status: SyncStatus
  last_synced_at: string | null
  pending_changes: number
  error_count_24h: number
}

// ── Service ──────────────────────────────────────────────────────────────────

const dashboardService = {
  async getKpiSummary(days = 30): Promise<KpiSummary> {
    const { data } = await apiClient.get<KpiSummary>(
      '/api/v1/dashboard/kpi-summary',
      { params: { days } },
    )
    return data
  },

  async getTodaySnapshot(): Promise<TodaySnapshot> {
    const { data } = await apiClient.get<TodaySnapshot>(
      '/api/v1/dashboard/today-snapshot',
    )
    return data
  },

  async getOccupancyTrend(days: 7 | 30 | 90 = 30): Promise<OccupancyDataPoint[]> {
    const { data } = await apiClient.get<unknown>(
      '/api/v1/dashboard/occupancy-trend',
      { params: { days } },
    )
    return ensureArray<OccupancyDataPoint>(data)
  },

  async getBookingSources(days = 30): Promise<BookingSource[]> {
    const { data } = await apiClient.get<unknown>(
      '/api/v1/dashboard/booking-sources',
      { params: { days } },
    )
    return ensureArray<BookingSource>(data)
  },

  async getChannelHealth(): Promise<ChannelHealthItem[]> {
    const { data } = await apiClient.get<unknown>('/api/v1/dashboard/channel-health')
    return ensureArray<ChannelHealthItem>(data)
  },

  async getRecentBookings(limit = 5): Promise<Reservation[]> {
    const { data } = await apiClient.get<unknown>(
      '/api/v1/reservations',
      { params: { page: 1, page_size: limit, sort_by: 'created_at', sort_dir: 'desc' } },
    )
    return ensureArray<Reservation>(data)
  },
}

export default dashboardService
