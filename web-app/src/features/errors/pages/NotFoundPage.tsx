import { Link } from 'react-router-dom'
import { ROUTES } from '@/router/routes'

export default function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
      <h1 className="text-6xl font-bold text-muted-foreground">404</h1>
      <p className="text-xl font-semibold">Page not found</p>
      <p className="text-muted-foreground">The page you're looking for doesn't exist.</p>
      <Link
        to={ROUTES.DASHBOARD}
        className="mt-2 text-sm text-brand-600 hover:underline"
      >
        Go to Dashboard
      </Link>
    </div>
  )
}
