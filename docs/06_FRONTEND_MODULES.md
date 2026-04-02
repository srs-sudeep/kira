# Frontend Modules — Screen-by-Screen Prompts

Each section is a prompt for one feature module. Build order: Auth → Dashboard → Rooms → Inventory Calendar → Reservations → Channels → Notifications → Settings.

---

## Module 1: Auth (Sprint 1)

**LoginPage.tsx:** Centered form, brand logo, email + password, React Hook Form + Zod validation. On submit: POST /auth/login. If mfa_required → redirect /mfa-verify. Store tokens in Zustand. Light/dark mode support.

**MfaVerifyPage.tsx:** 6-digit TOTP input. Auto-submit on 6 digits. POST /auth/login/mfa.

**ProtectedRoute.tsx:** No token → redirect /login. Expired → silent refresh. Loading spinner while checking.

---

## Module 2: Dashboard (Sprint 1)

**DashboardPage.tsx:**
- Greeting + date header
- 4 KPI cards: occupancy %, revenue MTD, check-ins today, active channels
- TodaySnapshot: mini-table (check-ins, check-outs, in-house, available)
- ChannelHealthPanel: row of OTA status badges (green/yellow/red + last sync)
- RecentBookings: latest 5 reservations mini-table (clickable → /reservations/{id})
- OccupancyChart: Recharts AreaChart, next 30 days
- BookingSourcePie: Recharts PieChart by channel

---

## Module 3: Rooms & Rate Plans (Sprint 2)

**RoomTypesPage.tsx:** Grid of RoomTypeCards (image, name, bedding, occupancy, inventory, rate plan count). "Add Room Type" button. Click → /rooms/{id}.

**RoomTypeDetailPage.tsx:** Top: room details (editable). Bottom: rate plan table with CRUD. "Add Rate Plan" opens side panel.

**RoomTypeForm.tsx:** RHF + Zod. Fields: name, description, max_occupancy, bedding_type (select), physical_inventory, amenities (multi-tag), images.

**RatePlanForm.tsx:** Fields: name, plan_type (select), base_amount, cancellation_policy, min/max LOS. Derived toggle: parent selector + type + value.

---

## Module 4: Inventory Calendar (Sprint 2) — CORE SCREEN

**CalendarPage.tsx:**
- Date range selector (default: today + 14d). Week/month navigation.
- Room type filter (dropdown or tabs).
- AriCalendarGrid component.

**AriCalendarGrid.tsx:** Spreadsheet-like grid.
- Rows: room type + rate plan combos, grouped by room type with sticky headers.
- Columns: dates. Weekend highlighting. Today highlight.
- Cells: rate (top) + available rooms (bottom). Color coded: green=high, yellow=low, red=sold out. Closed dates show strikethrough.

**AriCell.tsx:** Click → inline edit (rate, availability, min/max LOS). Enter=save, Escape=cancel. Tab=next cell. Optimistic update via React Query. Debounced save (300ms).

**BulkUpdateForm.tsx:** Wizard: select rooms → select dates → set values → review → confirm. POST /inventory/bulk-update.

**StopSellDialog.tsx:** Room types, channels, date range, CTA/CTD toggles. POST /inventory/stop-sell.

**Performance:** React.memo on cells. Single API call for grid data. Virtualise if >20 room types.

---

## Module 5: Reservations (Sprint 2)

**ReservationsPage.tsx:** "Reservations" header + "New Booking" button.
- Filter bar: status (multi-select), source (multi-select), date range, guest search.
- DataTable: confirmation #, guest, source (with OTA icon), room, check-in/out, nights, amount, status badge.
- Row click → /reservations/{id}. Pagination 25/50/100.

**ReservationDetailPage.tsx:**
- Left (2/3): details card, guest card, lifecycle timeline.
- Right (1/3): actions (modify, cancel, no-show), notes panel.

**CreateReservationDialog.tsx:** Full dialog. Guest info, room type (select), rate plan (filtered), dates, occupancy. Availability check on room+date select. Auto-calculate total. POST /reservations.

**ReservationNotes.tsx:** Chat-like. Each note: user, time, content. Add input at bottom.

---

## Module 6: Channels (Sprint 3)

**ChannelsPage.tsx:** Grid of ChannelCards (OTA logo, name, status badge, last sync, booking count). "Connect Channel" → /channels/connect.

**ConnectChannelWizard.tsx:** Step 1: select OTA (logo grid). Step 2: credentials. "Test Connection" button. Step 3: room/rate mapping (side-by-side selectors). Step 4: review + activate.

**ChannelDetailPage.tsx:** Tabs: Overview (status, sync, errors), Mappings (table + CRUD), Sync Log (DataTable: timestamp, type, status — click for payload detail), Settings (credentials, disconnect).

**ChannelHealthBadge.tsx:** Reusable. Green dot="Connected", yellow="Warning", red="Error".

---

## Module 7: Notifications (Sprint 3)

**NotificationBell.tsx:** Bell icon in Header with unread badge. Click → dropdown. Poll unread-count every 30s (React Query refetchInterval).

**NotificationDropdown.tsx:** Latest 5. Click item → mark read + navigate to relevant page (reservation, channel). "View All" → /notifications. "Mark All Read" button.

**NotificationsPage.tsx:** Full archive table. Filter by type, read/unread. Bulk mark read. Preferences section: toggle email/in-app per event type.

---

## Module 8: Settings (Sprint 1–3)

**PropertySettingsPage.tsx:** Edit tenant details form. Auto-save or explicit save.

**UserManagementPage.tsx:** DataTable of users (name, email, role, last login, MFA). "Invite User" dialog (email + role). Row actions: edit role, activate/deactivate.

**AuditLogPage.tsx:** DataTable with filters (action, user, dates). Click row → before/after diff in side panel. CSV export button.

**ProfilePage.tsx:** User info, password change, MFA setup/disable, active sessions list.
