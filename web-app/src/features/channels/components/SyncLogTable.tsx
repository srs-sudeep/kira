import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { type ColumnDef } from '@tanstack/react-table'
import { ChevronDown, ChevronRight, ArrowUpFromLine, ArrowDownToLine, RefreshCw } from 'lucide-react'
import { differenceInSeconds } from 'date-fns'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { DataTable } from '@/components/shared/DataTable'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { formatDateTime } from '@/lib/utils'
import channelsService from '../services/channels-service'
import type { SyncLog } from '@/types/channel'
import { DEFAULT_PAGE_SIZE } from '@/config/constants'

const SYNC_TYPE_LABELS: Record<string, string> = {
  ari_push:         'ARI Push',
  reservation_pull: 'Reservation Pull',
  full_sync:        'Full Sync',
}

const SYNC_TYPE_ICONS: Record<string, React.ElementType> = {
  ari_push:         ArrowUpFromLine,
  reservation_pull: ArrowDownToLine,
  full_sync:        RefreshCw,
}

function formatDuration(started: string, finished?: string): string {
  if (!finished) return '—'
  const secs = differenceInSeconds(new Date(finished), new Date(started))
  if (secs < 60) return `${secs}s`
  return `${Math.floor(secs / 60)}m ${secs % 60}s`
}

interface Props {
  channelId: string
}

export function SyncLogTable({ channelId }: Props) {
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string>('_all')
  const [expandedRow, setExpandedRow] = useState<string | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['channels', channelId, 'sync-log', { page, status: statusFilter }],
    queryFn: () =>
      channelsService.getSyncLog(channelId, {
        page,
        page_size: DEFAULT_PAGE_SIZE,
        status:
          statusFilter === '_all'
            ? undefined
            : (statusFilter as 'success' | 'failed' | 'partial'),
      }),
  })

  const columns: ColumnDef<SyncLog>[] = [
    {
      id: 'expand',
      header: '',
      size: 40,
      cell: ({ row }) =>
        row.original.error_message ? (
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={() =>
              setExpandedRow((p) =>
                p === row.original.id ? null : row.original.id,
              )
            }
          >
            {expandedRow === row.original.id ? (
              <ChevronDown className="h-3.5 w-3.5" />
            ) : (
              <ChevronRight className="h-3.5 w-3.5" />
            )}
          </Button>
        ) : null,
    },
    {
      accessorKey: 'sync_type',
      header: 'Type',
      cell: ({ getValue }) => {
        const type = getValue<string>()
        const Icon = SYNC_TYPE_ICONS[type] ?? RefreshCw
        return (
          <span className="flex items-center gap-1.5 text-sm">
            <Icon className="h-3.5 w-3.5 text-muted-foreground" />
            {SYNC_TYPE_LABELS[type] ?? type}
          </span>
        )
      },
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ getValue }) => <StatusBadge status={getValue<string>()} />,
    },
    {
      id: 'records',
      header: 'Records',
      cell: ({ row }) => {
        const { records_pushed, records_pulled } = row.original
        if (!records_pushed && !records_pulled)
          return <span className="text-muted-foreground text-xs">—</span>
        return (
          <div className="text-xs tabular-nums">
            {records_pushed !== undefined && (
              <div className="flex items-center gap-1">
                <ArrowUpFromLine className="h-3 w-3 text-muted-foreground" />
                {records_pushed} pushed
              </div>
            )}
            {records_pulled !== undefined && (
              <div className="flex items-center gap-1">
                <ArrowDownToLine className="h-3 w-3 text-muted-foreground" />
                {records_pulled} pulled
              </div>
            )}
          </div>
        )
      },
    },
    {
      accessorKey: 'started_at',
      header: 'Started',
      cell: ({ getValue }) => (
        <span className="text-xs tabular-nums">
          {formatDateTime(getValue<string>())}
        </span>
      ),
    },
    {
      id: 'duration',
      header: 'Duration',
      cell: ({ row }) => (
        <span className="text-xs tabular-nums text-muted-foreground">
          {formatDuration(row.original.started_at, row.original.finished_at)}
        </span>
      ),
    },
  ]

  return (
    <div className="space-y-4">
      {/* Filter */}
      <div className="flex items-center gap-2">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="h-9 w-36">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="_all">All statuses</SelectItem>
            <SelectItem value="success">Success</SelectItem>
            <SelectItem value="partial">Partial</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          {data?.total ?? 0} entries
        </p>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={data?.items ?? []}
        isLoading={isLoading}
        total={data?.total}
        page={page}
        pageSize={DEFAULT_PAGE_SIZE}
        onPageChange={setPage}
      />

      {/* Expanded error row */}
      {expandedRow && (() => {
        const row = data?.items.find((r) => r.id === expandedRow)
        return row?.error_message ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 p-4">
            <p className="mb-1 text-xs font-semibold text-destructive">Error Details</p>
            <pre className="whitespace-pre-wrap text-xs text-foreground">
              {row.error_message}
            </pre>
          </div>
        ) : null
      })()}
    </div>
  )
}
