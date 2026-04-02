import { apiClient } from '@/lib/api-client'
import type {
  LoginRequest,
  LoginResponse,
  RefreshResponse,
  ForgotPasswordRequest,
  ResetPasswordRequest,
  ChangePasswordRequest,
  MfaSetupResponse,
  User,
} from '@/types/auth'

const BASE = '/api/v1/auth'

export interface MfaLoginRequest {
  mfa_token: string
  totp_code: string
}

const authService = {
  async login(payload: LoginRequest): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>(`${BASE}/login`, payload)
    return data
  },

  async mfaLogin(payload: MfaLoginRequest): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>(`${BASE}/login/mfa`, payload)
    return data
  },

  async refresh(refreshToken: string): Promise<RefreshResponse> {
    const { data } = await apiClient.post<RefreshResponse>(`${BASE}/refresh`, {
      refresh_token: refreshToken,
    })
    return data
  },

  async forgotPassword(payload: ForgotPasswordRequest): Promise<void> {
    await apiClient.post(`${BASE}/forgot-password`, payload)
  },

  async resetPassword(payload: ResetPasswordRequest): Promise<void> {
    await apiClient.post(`${BASE}/reset-password`, payload)
  },

  async changePassword(payload: ChangePasswordRequest): Promise<void> {
    await apiClient.post(`${BASE}/change-password`, payload)
  },

  async getMe(): Promise<User> {
    const { data } = await apiClient.get<User>(`${BASE}/me`)
    return data
  },

  async updateMe(updates: Partial<Pick<User, 'full_name' | 'avatar_url'>>): Promise<User> {
    const { data } = await apiClient.patch<User>(`${BASE}/me`, updates)
    return data
  },

  async setupMfa(): Promise<MfaSetupResponse> {
    const { data } = await apiClient.post<MfaSetupResponse>(`${BASE}/mfa/setup`)
    return data
  },

  async verifyMfa(totp_code: string): Promise<{ backup_codes: string[] }> {
    const { data } = await apiClient.post<{ backup_codes: string[] }>(
      `${BASE}/mfa/verify`,
      { totp_code },
    )
    return data
  },

  async disableMfa(totp_code: string): Promise<void> {
    await apiClient.post(`${BASE}/mfa/disable`, { totp_code })
  },

  async logout(): Promise<void> {
    await apiClient.post(`${BASE}/logout`).catch(() => {
      // best-effort — always clear local state regardless
    })
  },
}

export default authService
