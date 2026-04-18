import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Building2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { QUERY_KEYS } from '@/config/constants'
import settingsService from '../services/settings-service'
import { PropertyForm } from '../components/PropertyForm'
import type { TenantUpdateRequest } from '@/types/tenant'

export default function PropertySettingsPage() {
  const qc = useQueryClient()

  const { data: tenant, isLoading } = useQuery({
    queryKey: QUERY_KEYS.SETTINGS.PROPERTY,
    queryFn: settingsService.getProperty,
  })

  const mutation = useMutation({
    mutationFn: (payload: TenantUpdateRequest) => settingsService.updateProperty(payload),
    onSuccess() {
      qc.invalidateQueries({ queryKey: QUERY_KEYS.SETTINGS.PROPERTY })
    },
  })

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-2">
        <Building2 className="h-5 w-5 text-muted-foreground" />
        <div>
          <h2 className="text-lg font-semibold">Property Details</h2>
          <p className="text-sm text-muted-foreground">Basic information about your hotel</p>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          {isLoading ? (
            <div className="space-y-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-9 w-full" />
              ))}
            </div>
          ) : (
            <PropertyForm
              tenant={tenant}
              onSubmit={mutation.mutate}
              isSubmitting={mutation.isPending}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
