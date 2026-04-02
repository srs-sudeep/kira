import { Outlet } from 'react-router-dom'
import { useUiStore } from '@/stores/ui-store'
import { cn } from '@/lib/utils'

export default function App() {
  const theme = useUiStore((s) => s.theme)

  return (
    <div className={cn(theme === 'dark' && 'dark')}>
      <Outlet />
    </div>
  )
}
