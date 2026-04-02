---
sidebar_position: 1
---

# Frontend Overview

The KIRA web-app is a React 19 + TypeScript SPA that serves as the property manager dashboard.

## Tech Stack

| Library | Version | Purpose |
|---|---|---|
| React | 19 | UI framework |
| TypeScript | 5.x | Static typing (`strict: true`) |
| Vite | 6.x | Build tool and dev server |
| Tailwind CSS | 4.x | Utility-first styling |
| shadcn/ui | latest | Base component library |
| TanStack Query | 5.x | Server state management |
| Zustand | 5.x | Client state management |
| React Router | 7.x | Client-side routing |
| React Hook Form | 7.x | Form state management |
| Zod | 3.x | Schema validation |
| TanStack Table | 8.x | Table component |
| axios | 1.x | HTTP client |
| bun | 1.x | Package manager |

## Project Structure

```
web-app/
├── src/
│   ├── components/          # Shared UI components
│   │   ├── layout/          # AppShell, Header, Sidebar
│   │   └── ui/              # shadcn/ui components
│   ├── features/            # Feature modules
│   │   ├── auth/            # Login, register
│   │   ├── dashboard/       # KPI overview
│   │   ├── rates/           # Rate & inventory management
│   │   ├── reservations/    # Booking management
│   │   ├── channels/        # OTA channel management
│   │   ├── notifications/   # Notification centre
│   │   ├── profile/         # User profile
│   │   └── settings/        # Property, users, audit log
│   ├── router/              # React Router config
│   ├── stores/              # Zustand stores
│   ├── services/            # API service layer (axios)
│   ├── types/               # TypeScript type definitions
│   ├── config/              # Constants, query keys, API config
│   ├── hooks/               # Shared custom hooks
│   └── lib/                 # Utilities
├── public/
├── index.html
├── package.json             # uses bun
├── vite.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

## Features at a Glance

| Feature | Route | Description |
|---|---|---|
| Dashboard | `/` | KPI cards, occupancy chart, recent bookings |
| Rates | `/rates` | Room types, rate plans, ARI calendar |
| Reservations | `/reservations` | Booking table, detail view, modify/cancel |
| Channels | `/channels` | OTA connections, mappings, sync log |
| Notifications | `/notifications` | Archive, bulk actions, preferences |
| Profile | `/profile` | Avatar, password, MFA |
| Settings | `/settings` | Property info, user management, audit log |

## Getting Started

```bash
cd web-app
bun install
bun run dev   # http://localhost:3000
```

For production build:

```bash
bun run build    # outputs to dist/
bun run preview  # preview prod build locally
```
