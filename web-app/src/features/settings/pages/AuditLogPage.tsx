import { ClipboardList } from 'lucide-react'
import { AuditLogTable } from '../components/AuditLogTable'

export default function AuditLogPage() {
  return (
    <div className="max-w-4xl space-y-6">
      <div className="flex items-center gap-2">
        <ClipboardList className="h-5 w-5 text-muted-foreground" />
        <div>
          <h2 className="text-lg font-semibold">Audit Log</h2>
          <p className="text-sm text-muted-foreground">
            A read-only record of all actions performed in your account
          </p>
        </div>
      </div>
      <AuditLogTable />
    </div>
  )
}
