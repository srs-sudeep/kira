import type { UserRole } from '@/config/constants'

export interface User {
  id: string
  email: string
  full_name: string
  role: UserRole
  tenant_id: string | null  // null for super_admin
  is_active: boolean
  avatar_url?: string
  last_login_at?: string
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
  totp_code?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
  /** Present after password login when MFA is not required */
  user?: User
  mfa_required?: boolean
  mfa_token?: string
}

export interface RefreshRequest {
  refresh_token: string
}

export interface RefreshResponse {
  access_token: string
  refresh_token: string
  expires_in: number
}

export interface ForgotPasswordRequest {
  email: string
}

export interface ResetPasswordRequest {
  token: string
  new_password: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}

export interface MfaSetupResponse {
  secret: string
  qr_code_uri: string
  backup_codes: string[]
}
