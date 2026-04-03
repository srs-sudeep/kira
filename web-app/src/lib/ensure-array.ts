/** Coerce unknown API payloads to T[] — prevents .map crashes when backend returns an object. */
export function ensureArray<T>(value: unknown): T[] {
  if (Array.isArray(value)) return value
  if (value && typeof value === 'object' && 'items' in value) {
    const items = (value as { items: unknown }).items
    if (Array.isArray(items)) return items as T[]
  }
  return []
}
