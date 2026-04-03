import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { AppErrorBoundary } from '@/components/shared/AppErrorBoundary'
import { useUiStore } from '@/stores/ui-store'

export default function App() {
  const theme = useUiStore((s) => s.theme)
  const accentColor = useUiStore((s) => s.accentColor)

  useEffect(() => {
    useUiStore.getState().setTheme(theme)
  }, [theme])

  useEffect(() => {
    useUiStore.getState().setAccentColor(accentColor)
  }, [accentColor])

  return (
    <AppErrorBoundary>
      <Outlet />
    </AppErrorBoundary>
  )
}
