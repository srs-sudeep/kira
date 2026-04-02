export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? '/api'

export const APP_NAME = 'KIRA'
export const APP_VERSION: string = import.meta.env.VITE_APP_VERSION ?? '0.1.0'

export const IS_DEV = import.meta.env.DEV
export const IS_PROD = import.meta.env.PROD
