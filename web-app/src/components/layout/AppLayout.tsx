import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useUiStore } from '@/stores/ui-store'
import { cn } from '@/lib/utils'

export function AppLayout() {
  const sidebarCollapsed = useUiStore((s) => s.sidebarCollapsed)

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />

      <div
        className={cn(
          'flex flex-1 flex-col overflow-hidden transition-all duration-300 ease-in-out',
          sidebarCollapsed ? 'ml-[72px]' : 'ml-[272px]',
        )}
      >
        <Header />

        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1400px] p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
