import type { AxiosError } from 'axios'

/** FastAPI / Pydantic: `detail` may be a string, object, or list of validation errors */
type ValidationErr = {
  type?: string
  loc?: (string | number)[]
  msg?: string
  input?: unknown
}

function formatDetail(detail: unknown): string | null {
  if (detail == null) return null
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      if (typeof item === 'string') return item
      if (item && typeof item === 'object' && 'msg' in item) {
        const v = item as ValidationErr
        const loc = Array.isArray(v.loc) ? v.loc.map(String).filter(Boolean).join('.') : ''
        const msg = v.msg ?? 'Invalid value'
        return loc ? `${loc}: ${msg}` : msg
      }
      try {
        return JSON.stringify(item)
      } catch {
        return String(item)
      }
    })
    return parts.join(' ')
  }
  if (typeof detail === 'object' && detail !== null) {
    const o = detail as Record<string, unknown>
    if (typeof o.msg === 'string') return o.msg
    if (typeof o.message === 'string') return o.message
  }
  return String(detail)
}

/** Human-readable message from an Axios error body (handles 422 validation arrays). */
export function getAxiosApiErrorMessage(
  error: unknown,
  fallback = 'Something went wrong',
): string {
  const ax = error as AxiosError<{ detail?: unknown; message?: string }>
  const data = ax.response?.data
  if (!data) return ax.message || fallback
  const fromDetail = formatDetail(data.detail)
  if (fromDetail) return fromDetail
  if (typeof data.message === 'string') return data.message
  return fallback
}
