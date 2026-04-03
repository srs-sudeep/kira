// Empty default: axios uses paths like `/api/v1/...` as-is; Vite proxies `/api` → Kong.
// Set VITE_API_BASE_URL only for an absolute gateway origin (e.g. https://api.example.com).
export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? ''

export const APP_NAME = 'KIRA'
export const APP_VERSION: string = import.meta.env.VITE_APP_VERSION ?? '0.1.0'

export const IS_DEV = import.meta.env.DEV
export const IS_PROD = import.meta.env.PROD
