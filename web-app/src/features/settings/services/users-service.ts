import { apiClient } from '@/lib/api-client'
import type { User } from '@/types/auth'
import type { UserRole } from '@/config/constants'
import type { PaginatedResponse } from '@/types/api'

const BASE = '/api/v1/users'

export interface UserListParams {
  page?: number
  page_size?: number
  search?: string
  role?: UserRole
  is_active?: boolean
}

export interface InviteUserPayload {
  email: string
  full_name: string
  role: Exclude<UserRole, 'super_admin'>
}

const usersService = {
  async list(params?: UserListParams): Promise<PaginatedResponse<User>> {
    const { data } = await apiClient.get<PaginatedResponse<User>>(BASE, { params })
    return data
  },

  async get(id: string): Promise<User> {
    const { data } = await apiClient.get<User>(`${BASE}/${id}`)
    return data
  },

  async invite(payload: InviteUserPayload): Promise<User> {
    const { data } = await apiClient.post<User>(`${BASE}/invite`, payload)
    return data
  },

  async updateRole(id: string, role: UserRole): Promise<User> {
    const { data } = await apiClient.patch<User>(`${BASE}/${id}`, { role })
    return data
  },

  async deactivate(id: string): Promise<User> {
    const { data } = await apiClient.post<User>(`${BASE}/${id}/deactivate`)
    return data
  },

  async reactivate(id: string): Promise<User> {
    const { data } = await apiClient.post<User>(`${BASE}/${id}/reactivate`)
    return data
  },

  async resendInvite(id: string): Promise<void> {
    await apiClient.post(`${BASE}/${id}/resend-invite`)
  },
}

export default usersService
