import { lazy, Suspense } from 'react'
import { createBrowserRouter, Navigate } from 'react-router-dom'
import App from '@/App'
import { ProtectedRoute } from './ProtectedRoute'
import { RoleGuard } from './RoleGuard'
import { ROUTES } from './routes'
import { USER_ROLES } from '@/config/constants'
import { LoadingState } from '@/components/shared/LoadingState'
import { AppLayout } from '@/components/layout/AppLayout'

// Auth pages
const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage'))
const MfaVerifyPage = lazy(() => import('@/features/auth/pages/MfaVerifyPage'))
const ForgotPasswordPage = lazy(() => import('@/features/auth/pages/ForgotPasswordPage'))
const ResetPasswordPage = lazy(() => import('@/features/auth/pages/ResetPasswordPage'))

// App pages
const DashboardPage = lazy(() => import('@/features/dashboard/pages/DashboardPage'))

// Rooms & Inventory
const RoomsPage = lazy(() => import('@/features/rooms/pages/RoomsPage'))
const RoomDetailPage = lazy(() => import('@/features/rooms/pages/RoomDetailPage'))
const RatePlansPage = lazy(() => import('@/features/rooms/pages/RatePlansPage'))
const InventoryCalendarPage = lazy(() => import('@/features/inventory/pages/InventoryCalendarPage'))
const SeasonalRulesPage = lazy(() => import('@/features/inventory/pages/SeasonalRulesPage'))

// Reservations
const ReservationsPage = lazy(() => import('@/features/reservations/pages/ReservationsPage'))
const ReservationDetailPage = lazy(() => import('@/features/reservations/pages/ReservationDetailPage'))

// Channels
const ChannelsPage = lazy(() => import('@/features/channels/pages/ChannelsPage'))
const ChannelDetailPage = lazy(() => import('@/features/channels/pages/ChannelDetailPage'))

// Notifications
const NotificationsPage = lazy(() => import('@/features/notifications/pages/NotificationsPage'))

// Profile / Settings
const ProfilePage = lazy(() => import('@/features/profile/pages/ProfilePage'))
const SettingsPage = lazy(() => import('@/features/profile/pages/SettingsPage'))
const PropertySettingsPage = lazy(() => import('@/features/settings/pages/PropertySettingsPage'))
const UserManagementPage = lazy(() => import('@/features/settings/pages/UserManagementPage'))
const AuditLogPage = lazy(() => import('@/features/settings/pages/AuditLogPage'))

// Admin (super_admin)
const AdminTenantsPage = lazy(() => import('@/features/admin/pages/AdminTenantsPage'))
const AdminTenantDetailPage = lazy(() => import('@/features/admin/pages/AdminTenantDetailPage'))
const AdminUsersPage = lazy(() => import('@/features/admin/pages/AdminUsersPage'))

// 404
const NotFoundPage = lazy(() => import('@/features/errors/pages/NotFoundPage'))

function SuspenseFallback() {
  return <LoadingState message="Loading…" fullScreen />
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      // Public auth routes
      {
        path: ROUTES.LOGIN,
        element: (
          <Suspense fallback={<SuspenseFallback />}>
            <LoginPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.MFA_VERIFY,
        element: (
          <Suspense fallback={<SuspenseFallback />}>
            <MfaVerifyPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.FORGOT_PASSWORD,
        element: (
          <Suspense fallback={<SuspenseFallback />}>
            <ForgotPasswordPage />
          </Suspense>
        ),
      },
      {
        path: ROUTES.RESET_PASSWORD,
        element: (
          <Suspense fallback={<SuspenseFallback />}>
            <ResetPasswordPage />
          </Suspense>
        ),
      },

      // Protected app routes
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppLayout />,
            children: [
              // Root redirect
              { index: true, element: <Navigate to={ROUTES.DASHBOARD} replace /> },

              // Dashboard
              {
                path: ROUTES.DASHBOARD,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <DashboardPage />
                  </Suspense>
                ),
              },

              // Rooms
              {
                path: ROUTES.ROOMS,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <RoomsPage />
                  </Suspense>
                ),
              },
              {
                path: ROUTES.ROOM_DETAIL,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <RoomDetailPage />
                  </Suspense>
                ),
              },
              {
                path: ROUTES.RATE_PLANS,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <RatePlansPage />
                  </Suspense>
                ),
              },

              // Inventory
              {
                path: ROUTES.INVENTORY_CALENDAR,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <InventoryCalendarPage />
                  </Suspense>
                ),
              },
              {
                path: ROUTES.SEASONAL_RULES,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <SeasonalRulesPage />
                  </Suspense>
                ),
              },

              // Reservations
              {
                path: ROUTES.RESERVATIONS,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <ReservationsPage />
                  </Suspense>
                ),
              },
              {
                path: ROUTES.RESERVATION_DETAIL,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <ReservationDetailPage />
                  </Suspense>
                ),
              },

              // Channels
              {
                path: ROUTES.CHANNELS,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <ChannelsPage />
                  </Suspense>
                ),
              },
              {
                path: ROUTES.CHANNEL_DETAIL,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <ChannelDetailPage />
                  </Suspense>
                ),
              },

              // Notifications
              {
                path: ROUTES.NOTIFICATIONS,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <NotificationsPage />
                  </Suspense>
                ),
              },

              // Profile & Settings
              {
                path: ROUTES.PROFILE,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <ProfilePage />
                  </Suspense>
                ),
              },
              {
                path: ROUTES.SETTINGS,
                element: (
                  <Suspense fallback={<SuspenseFallback />}>
                    <SettingsPage />
                  </Suspense>
                ),
                children: [
                  {
                    index: true,
                    element: (
                      <Suspense fallback={<SuspenseFallback />}>
                        <PropertySettingsPage />
                      </Suspense>
                    ),
                  },
                  {
                    path: 'users',
                    element: (
                      <Suspense fallback={<SuspenseFallback />}>
                        <UserManagementPage />
                      </Suspense>
                    ),
                  },
                  {
                    path: 'audit-log',
                    element: (
                      <Suspense fallback={<SuspenseFallback />}>
                        <AuditLogPage />
                      </Suspense>
                    ),
                  },
                ],
              },

              // Admin — super_admin only
              {
                element: (
                  <RoleGuard allowedRoles={[USER_ROLES.SUPER_ADMIN]} />
                ),
                children: [
                  {
                    path: ROUTES.ADMIN_TENANTS,
                    element: (
                      <Suspense fallback={<SuspenseFallback />}>
                        <AdminTenantsPage />
                      </Suspense>
                    ),
                  },
                  {
                    path: ROUTES.ADMIN_TENANT_DETAIL,
                    element: (
                      <Suspense fallback={<SuspenseFallback />}>
                        <AdminTenantDetailPage />
                      </Suspense>
                    ),
                  },
                  {
                    path: ROUTES.ADMIN_USERS,
                    element: (
                      <Suspense fallback={<SuspenseFallback />}>
                        <AdminUsersPage />
                      </Suspense>
                    ),
                  },
                ],
              },
            ],
          },
        ],
      },

      // 404
      {
        path: ROUTES.NOT_FOUND,
        element: (
          <Suspense fallback={<SuspenseFallback />}>
            <NotFoundPage />
          </Suspense>
        ),
      },
    ],
  },
])
