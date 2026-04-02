import { apiClient } from '@/lib/api-client'
import type { Tenant, TenantUpdateRequest } from '@/types/tenant'
import type { PaginatedResponse } from '@/types/api'

const BASE = '/api/v1/settings'

export interface AuditLogEntry {
  id: string
  timestamp: string
  user_id: string
  user_name: string
  user_email: string
  action: string              // e.g. 'reservation.created'
  resource_type: string       // e.g. 'reservation'
  resource_id?: string
  ip_address?: string
  user_agent?: string
  details?: Record<string, unknown>
}

export interface AuditLogParams {
  page?: number
  page_size?: number
  user_id?: string
  action?: string
  from?: string
  to?: string
}

const settingsService = {
  // ── Property / Tenant settings ────────────────────────────────────────────

  async getProperty(): Promise<Tenant> {
    const { data } = await apiClient.get<Tenant>(`${BASE}/property`)
    return data
  },

  async updateProperty(payload: TenantUpdateRequest): Promise<Tenant> {
    const { data } = await apiClient.patch<Tenant>(`${BASE}/property`, payload)
    return data
  },

  async uploadLogo(file: File): Promise<{ logo_url: string }> {
    const form = new FormData()
    form.append('file', file)
    const { data } = await apiClient.post<{ logo_url: string }>(
      `${BASE}/property/logo`,
      form,
      { headers: { 'Content-Type': 'multipart/form-data' } },
    )
    return data
  },

  // ── Audit Log ────────────────────────────────────────────────────────────────

  async getAuditLog(params: AuditLogParams): Promise<PaginatedResponse<AuditLogEntry>> {
    const { data } = await apiClient.get<PaginatedResponse<AuditLogEntry>>(
      `${BASE}/audit-log`,
      { params },
    )
    return data
  },
}

export default settingsService
