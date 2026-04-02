---
sidebar_position: 2
---

# Authentication API

Base path: `/identity/auth/` (via Kong) or `http://localhost:8001/auth/` (direct)

## POST /auth/login

Authenticate a user and receive tokens.

**Request:**
```json
{
  "email": "manager@grandhotel.com",
  "password": "SecurePassword123!",
  "mfa_code": "123456"
}
```

`mfa_code` is required only if the user has MFA enabled.

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "manager@grandhotel.com",
    "full_name": "John Manager",
    "role": "manager",
    "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
    "avatar_url": null,
    "mfa_enabled": true,
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z"
  }
}
```

The refresh token is set as an HttpOnly cookie (`kira_refresh_token`).

**Response 401:**
```json
{ "detail": "Invalid credentials" }
```

**Response 403 (MFA required):**
```json
{ "detail": "MFA code required", "code": "MFA_REQUIRED" }
```

---

## POST /auth/refresh

Exchange refresh token for a new access token.

The refresh token is read from the HttpOnly cookie automatically.

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## POST /auth/logout

Revoke the refresh token.

**Response 204:** No content.

---

## GET /auth/me

Get the current authenticated user.

**Response 200:**
```json
{
  "id": "uuid",
  "email": "manager@grandhotel.com",
  "full_name": "John Manager",
  "role": "manager",
  "tenant_id": "uuid",
  "avatar_url": "https://cdn.kira.abodeab.com/avatars/uuid.jpg",
  "mfa_enabled": true,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "last_login_at": "2025-06-15T09:00:00Z"
}
```

---

## PATCH /auth/me

Update the current user's profile.

**Request:**
```json
{
  "full_name": "John Updated",
  "avatar_url": "https://cdn.kira.abodeab.com/avatars/new.jpg"
}
```

All fields are optional. Only `full_name` and `avatar_url` can be updated here.

---

## POST /auth/change-password

**Request:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

**Response 204:** No content.  
**Response 400:** `{ "detail": "Current password is incorrect" }`

---

## POST /auth/mfa/setup

Generate a TOTP secret and QR code for MFA setup.

**Response 200:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_uri": "otpauth://totp/KIRA:manager@grandhotel.com?secret=JBSWY3DPEHPK3PXP&issuer=KIRA"
}
```

---

## POST /auth/mfa/verify

Enable MFA by confirming a 6-digit TOTP code.

**Request:**
```json
{ "code": "123456" }
```

**Response 200:**
```json
{
  "backup_codes": [
    "ABCD-EFGH", "IJKL-MNOP", "QRST-UVWX",
    "YZAB-CDEF", "GHIJ-KLMN", "OPQR-STUV",
    "WXYZ-0123", "4567-89AB"
  ]
}
```

Store backup codes securely — they are shown only once.
