---
sidebar_position: 4
---

# Feature Modules

Each major section of the dashboard is organized as a self-contained feature module under `src/features/`.

## Module Structure

```
src/features/<name>/
├── pages/          # Route-level page components
├── components/     # Feature-specific components
├── services/       # API service functions
└── (hooks/)        # Feature-specific hooks (if needed)
```

## Feature: Auth (`src/features/auth/`)

Handles login, registration, and token management.

**Pages:** `LoginPage`, `RegisterPage`  
**Services:** `authService` — login, register, logout, me, changePassword, updateMe, MFA

## Feature: Dashboard (`src/features/dashboard/`)

KPI overview and quick-access widgets.

**Pages:** `DashboardPage`  
**Components:** `KpiCard`, `OccupancyChart`, `RecentBookingsTable`, `ChannelStatusWidget`

## Feature: Rates (`src/features/rates/`)

Room type and rate plan management with ARI calendar.

**Pages:** `RatesPage`, `RoomTypeDetailPage`  
**Components:**
- `RoomTypeCard` — room type summary card
- `RoomTypeForm` — create/edit form
- `RatePlanList` — table of rate plans for a room type
- `RatePlanForm` — create/edit form
- `ARICalendar` — date-grid calendar showing rates and availability
- `BulkUpdateModal` — bulk ARI update across a date range

## Feature: Reservations (`src/features/reservations/`)

Booking management with modification and cancellation.

**Pages:** `ReservationsPage`, `ReservationDetailPage`  
**Components:**
- `ReservationTable` — paginated table with filters (status, channel, date)
- `ReservationStatusBadge` — color-coded status pill
- `ModifyReservationSheet` — side sheet for date/room changes
- `CancelReservationDialog` — cancellation with refund preview

## Feature: Channels (`src/features/channels/`)

OTA channel connections and sync management.

**Pages:** `ChannelsPage`, `ChannelDetailPage`  
**Components:**
- `ChannelCard` — card showing OTA logo, status, last sync
- `ConnectChannelWizard` — multi-step wizard: select OTA → enter credentials → test connection → map rooms
- `ChannelMappingTable` — room type / rate plan mapping editor
- `SyncLogTable` — paginated sync history with status badges

## Feature: Notifications (`src/features/notifications/`)

In-app notification centre.

**Pages:** `NotificationsPage`  
**Components:**
- `NotificationBell` — header icon with unread badge (polls every 30s)
- `NotificationDropdown` — popover with recent notifications

## Feature: Profile (`src/features/profile/`)

User profile editing, password change, and MFA.

**Pages:** `ProfilePage`  
**Components:** `MfaSetupCard` — TOTP setup wizard (QR → verify → backup codes)

## Feature: Settings (`src/features/settings/`)

Property settings, user management, and audit log. Uses a nested layout with side-nav.

**Pages:** `SettingsPage` (layout), `PropertySettingsPage`, `UserManagementPage`, `AuditLogPage`  
**Components:**
- `PropertyForm` — hotel details form
- `InviteUserDialog` — invite user by email + role
- `UserTable` — team members with inline role change
- `AuditLogTable` — expandable rows with action details

## Adding a New Feature Module

1. Create `src/features/<name>/` with `pages/`, `components/`, `services/`
2. Add service file: `src/features/<name>/services/<name>Service.ts`
3. Add query keys to `src/config/constants.ts`
4. Add route(s) to `src/router/index.tsx`
5. Add route constant(s) to `src/router/routes.ts`
6. Add nav item to `src/components/layout/Sidebar.tsx` if needed
