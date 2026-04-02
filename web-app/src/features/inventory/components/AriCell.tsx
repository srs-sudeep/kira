import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { cn } from '@/lib/utils'
import type { InventoryDay } from '@/types/inventory'

interface AriCellProps {
  day: InventoryDay | undefined
  onSave: (updates: { rate?: number; available_rooms?: number }) => Promise<void>
}

function cellColorClass(day: InventoryDay | undefined): string {
  if (!day) return 'bg-muted/30 text-muted-foreground'
  if (day.stop_sell || day.is_closed)
    return 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-400'
  if (day.available_rooms === 0)
    return 'bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400'
  if (day.available_rooms <= 2)
    return 'bg-yellow-50 text-yellow-700 dark:bg-yellow-950/40 dark:text-yellow-400'
  return 'bg-green-50 text-green-700 dark:bg-green-950/40 dark:text-green-400'
}

function formatRate(rate: number): string {
  // Compact: 5000 → 5k, 12500 → 12.5k
  if (rate >= 1000) return `${(rate / 1000).toFixed(rate % 1000 === 0 ? 0 : 1)}k`
  return String(rate)
}

export function AriCell({ day, onSave }: AriCellProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [editRate, setEditRate] = useState('')
  const [editAvail, setEditAvail] = useState('')
  const rateRef = useRef<HTMLInputElement>(null)

  function enterEdit() {
    if (!day || isSaving) return
    setEditRate(String(day.rate))
    setEditAvail(String(day.available_rooms))
    setIsEditing(true)
  }

  useEffect(() => {
    if (isEditing) {
      rateRef.current?.focus()
      rateRef.current?.select()
    }
  }, [isEditing])

  async function handleSave() {
    if (!day) return
    const newRate = parseFloat(editRate)
    const newAvail = parseInt(editAvail, 10)
    const updates: { rate?: number; available_rooms?: number } = {}
    if (!isNaN(newRate) && newRate !== day.rate) updates.rate = newRate
    if (!isNaN(newAvail) && newAvail !== day.available_rooms)
      updates.available_rooms = newAvail

    if (Object.keys(updates).length === 0) {
      setIsEditing(false)
      return
    }

    setIsSaving(true)
    try {
      await onSave(updates)
      setIsEditing(false)
    } finally {
      setIsSaving(false)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleSave()
    } else if (e.key === 'Escape') {
      setIsEditing(false)
    } else if (e.key === 'Tab') {
      // allow natural tab between rate and avail inputs
    }
  }

  // ── View mode ────────────────────────────────────────────────────────────────
  if (!isEditing) {
    return (
      <button
        type="button"
        onClick={enterEdit}
        disabled={isSaving}
        title={
          day
            ? `Rate: ₹${day.rate} | Available: ${day.available_rooms}${day.stop_sell ? ' | Stop Sell' : ''}${day.is_closed ? ' | Closed' : ''}`
            : 'No data'
        }
        className={cn(
          'flex h-12 w-full flex-col items-center justify-center gap-0.5 px-1 text-center',
          'transition-opacity hover:opacity-80',
          isSaving && 'opacity-50 cursor-wait',
          cellColorClass(day),
        )}
      >
        {day ? (
          <>
            <span className="text-xs font-semibold leading-none">
              ₹{formatRate(day.rate)}
            </span>
            <span className="text-[10px] leading-none opacity-80">
              {day.stop_sell ? 'STOP' : day.is_closed ? 'CLOSED' : `${day.available_rooms}`}
            </span>
          </>
        ) : (
          <span className="text-[10px] opacity-40">—</span>
        )}
      </button>
    )
  }

  // ── Edit mode ────────────────────────────────────────────────────────────────
  return (
    <div
      className={cn(
        'flex h-12 w-full flex-col items-center justify-center gap-0.5 px-1',
        'ring-2 ring-brand-500 ring-inset bg-card z-10',
      )}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
          handleSave()
        }
      }}
    >
      <input
        ref={rateRef}
        type="number"
        value={editRate}
        onChange={(e) => setEditRate(e.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full bg-transparent text-center text-xs font-semibold outline-none tabular-nums"
        placeholder="Rate"
        min={0}
        step={1}
      />
      <input
        type="number"
        value={editAvail}
        onChange={(e) => setEditAvail(e.target.value)}
        onKeyDown={handleKeyDown}
        className="w-full bg-transparent text-center text-[10px] outline-none tabular-nums text-muted-foreground"
        placeholder="Avail"
        min={0}
        step={1}
      />
    </div>
  )
}
