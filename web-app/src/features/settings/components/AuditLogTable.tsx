import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Filter, ChevronDown, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'
import { QUERY_KEYS } from '@/config/constants'
import { format, parseISO } from 'date-fns'
import settingsService from '../services/settings-service'
import type { AuditLogParams } from '../services/settings-service'

const ACTION_COLORS: Record<string, string> = {
  created: 'bg-accent-50 text-accent-700 border-accent-200',
  modified: 'bg-blue-50 text-blue-700 border-blue-200',
  deleted: 'bg-red-50 text-red-700 border-red-200',
  login: 'bg-purple-50 text-purple-700 border-purple-200',
  logout: 'bg-gray-50 text-gray-600 border-gray-200',
}

function actionColor(action: string): string {
  const verb = action.split('.').pop() ?? ''
  return ACTION_COLORS[verb] ?? 'bg-muted text-muted-foreground border-border'
}

interface ExpandableRowProps {
  entry: Awaited<ReturnType<typeof settingsService.getAuditLog>>['items'][number]
}

function AuditRow({ entry }: ExpandableRowProps) {
  const [expanded, setExpanded] = useState(false)
  const hasDetails = entry.details && Object.keys(entry.details).length > 0

  return (
    <>
      <div className="flex items-center gap-3 px-4 py-3 hover:bg-muted/30">
        <button
          type="button"
          className="shrink-0 text-muted-foreground"
          onClick={() => setExpanded((e) => !e)}
          disabled={!hasDetails}
          aria-label={expanded ? 'Collapse details' : 'Expand details'}
        >
          {hasDetails
            ? expanded
              ? <ChevronDown className="h-4 w-4" />
              : <ChevronRight className="h-4 w-4" />
            : <span className="h-4 w-4 block" />}
        </button>

        <div className="min-w-0 flex-1 grid grid-cols-[minmax(0,1fr)_8rem_7rem_7rem] items-center gap-3">
          {/* Action */}
          <div className="flex items-center gap-2 min-w-0">
            <Badge
              variant="outline"
              className={cn('shrink-0 text-[10px] font-mono', actionColor(entry.action))}
            >
              {entry.action}
            </Badge>
            {entry.resource_type && (
              <span className="truncate text-xs text-muted-foreground">
                {entry.resource_type}
                {entry.resource_id && (
                  <span className="ml-1 font-mono text-[11px]">#{entry.resource_id.slice(0, 8)}</span>
                )}
              </span>
            )}
          </div>

          {/* User */}
          <p className="truncate text-xs">{entry.user_name}</p>

          {/* IP */}
          <p className="text-xs text-muted-foreground font-mono">{entry.ip_address ?? '—'}</p>

          {/* Time */}
          <p className="text-xs text-muted-foreground text-right">
            {format(parseISO(entry.timestamp), 'dd MMM, HH:mm')}
          </p>
        </div>
      </div>

      {expanded && hasDetails && (
        <div className="border-t bg-muted/20 px-10 py-3">
          <pre className="text-[11px] text-muted-foreground overflow-auto max-h-40">
            {JSON.stringify(entry.details, null, 2)}
          </pre>
        </div>
      )}
    </>
  )
}

export function AuditLogTable() {
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState<AuditLogParams>({})

  const params: AuditLogParams = { page, page_size: 25, ...filters }

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEYS.SETTINGS.AUDIT_LOG(params),
    queryFn: () => settingsService.getAuditLog(params),
  })

  const entries = data?.items ?? []
  const totalPages = data ? Math.ceil(data.total / (data.page_size)) : 1

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3">
        <Filter className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Filter by action…"
          value={filters.action ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, action: e.target.value || undefined })); setPage(1) }}
          className="h-8 w-52 text-xs"
        />
        <Input
          type="date"
          value={filters.from ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, from: e.target.value || undefined })); setPage(1) }}
          className="h-8 w-40 text-xs"
        />
        <Input
          type="date"
          value={filters.to ?? ''}
          onChange={(e) => { setFilters((f) => ({ ...f, to: e.target.value || undefined })); setPage(1) }}
          className="h-8 w-40 text-xs"
        />
      </div>

      {/* Table */}
      <div className="rounded-lg border overflow-hidden">
        {/* Column headers */}
        <div className="flex items-center gap-3 border-b bg-muted/50 px-4 py-2">
          <span className="h-4 w-4 shrink-0" />
          <div className="flex-1 grid grid-cols-[minmax(0,1fr)_8rem_7rem_7rem] gap-3">
            <span className="text-xs font-medium text-muted-foreground">Action</span>
            <span className="text-xs font-medium text-muted-foreground">User</span>
            <span className="text-xs font-medium text-muted-foreground">IP Address</span>
            <span className="text-xs font-medium text-muted-foreground text-right">Time</span>
          </div>
        </div>

        {isLoading ? (
          <div className="divide-y">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-3">
                <Skeleton className="h-4 w-4" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </div>
        ) : entries.length === 0 ? (
          <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
            No audit log entries found
          </div>
        ) : (
          <div className="divide-y">
            {entries.map((entry) => (
              <AuditRow key={entry.id} entry={entry} />
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">Page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              Previous
            </Button>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
