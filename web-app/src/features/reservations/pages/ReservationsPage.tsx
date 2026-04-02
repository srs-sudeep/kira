import { useState, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { PageHeader } from '@/components/shared/PageHeader'
import { ReservationTable } from '../components/ReservationTable'
import { ReservationFilters } from '../components/ReservationFilters'
import { CreateReservationDialog } from '../components/CreateReservationDialog'
import type { ReservationListParams } from '@/types/reservation'
import reservationsService from '../services/reservations-service'
import { DEFAULT_PAGE_SIZE } from '@/config/constants'

const DEFAULT_FILTERS: ReservationListParams = {
  page: 1,
  page_size: DEFAULT_PAGE_SIZE,
  sort_by: 'created_at',
  sort_dir: 'desc',
}

export default function ReservationsPage() {
  const [filters, setFilters] = useState<ReservationListParams>(DEFAULT_FILTERS)
  const [createOpen, setCreateOpen] = useState(false)

  const queryKey = ['reservations', filters] as const

  const { data, isLoading } = useQuery({
    queryKey,
    queryFn: () => reservationsService.list(filters),
  })

  const handleFiltersChange = useCallback((next: ReservationListParams) => {
    setFilters(next)
  }, [])

  return (
    <>
      <PageHeader
        title="Reservations"
        description={
          data ? `${data.total.toLocaleString()} total reservations` : undefined
        }
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-1.5 h-4 w-4" />
            New Reservation
          </Button>
        }
      />

      <div className="space-y-4">
        <ReservationFilters filters={filters} onChange={handleFiltersChange} />

        <ReservationTable
          data={data?.items ?? []}
          isLoading={isLoading}
          total={data?.total}
          page={filters.page}
          pageSize={filters.page_size}
          onPageChange={(page) => setFilters((f) => ({ ...f, page }))}
          onPageSizeChange={(page_size) =>
            setFilters((f) => ({ ...f, page_size, page: 1 }))
          }
        />
      </div>

      <CreateReservationDialog open={createOpen} onOpenChange={setCreateOpen} />
    </>
  )
}
