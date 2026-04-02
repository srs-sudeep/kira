# Frontend Architecture — React + TypeScript + TailwindCSS

## Context
React 18+ SPA for the Abode@AB Channel Manager admin dashboard. Communicates with backend microservices through the Kong API Gateway at `/api/v1/`. The frontend doesn't know about individual services — it talks to one gateway URL.

## Key Difference from Monolith
The frontend code is IDENTICAL regardless of whether the backend is monolith or microservices. The API Gateway (Kong) routes requests transparently:
- `/api/v1/auth/*` → Identity Service :8001
- `/api/v1/rooms/*` → Rate & Inventory Service :8002
- `/api/v1/inventory/*` → Rate & Inventory Service :8002
- `/api/v1/reservations/*` → Reservation Service :8003
- `/api/v1/channels/*` → Channel Engine :8004
- `/api/v1/notifications/*` → Notification Service :8005
- `/api/v1/tenants/*` → Admin Service :8006
- `/api/v1/users/*` → Identity Service :8001
- `/api/v1/audit/*` → Identity Service :8001

The React app just calls `/api/v1/...` — Kong handles the routing.

## Tech Stack
- React 18+ with TypeScript 5.4+
- Vite 5+ (build tool)
- Tailwind CSS 3.4+ with shadcn/ui components
- TanStack Query 5+ (server state)
- Zustand 4+ (client state)
- React Router 6+ (routing)
- React Hook Form + Zod (forms)
- TanStack Table 8+ (data tables)
- Recharts 2+ (charts)
- Axios (HTTP client with JWT interceptor)

## Folder Structure

```
web-app/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── config/
│   │   ├── index.ts                  # API base URL, feature flags
│   │   └── constants.ts              # Enums, role names, status labels
│   ├── lib/
│   │   ├── api-client.ts             # Axios instance (auth interceptor, token refresh)
│   │   ├── query-client.ts           # TanStack Query config
│   │   ├── utils.ts                  # cn(), formatCurrency, formatDate
│   │   └── storage.ts                # localStorage wrappers
│   ├── types/                        # TypeScript interfaces for all API entities
│   │   ├── api.ts, auth.ts, tenant.ts, room.ts, inventory.ts
│   │   ├── reservation.ts, channel.ts, notification.ts
│   ├── hooks/                        # Shared hooks
│   │   ├── use-auth.ts, use-theme.ts, use-debounce.ts, use-pagination.ts
│   ├── stores/                       # Zustand stores
│   │   ├── auth-store.ts             # user, tokens, tenant
│   │   └── ui-store.ts               # sidebar, theme, modals
│   ├── components/
│   │   ├── ui/                       # shadcn/ui (auto-generated)
│   │   ├── layout/                   # AppLayout, Sidebar, Header, Breadcrumb
│   │   ├── shared/                   # DataTable, PageHeader, EmptyState, StatusBadge, etc.
│   │   └── charts/                   # OccupancyChart, RevenueChart, BookingSourcePie
│   ├── features/                     # Domain modules (see 06_FRONTEND_MODULES.md)
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── rooms/
│   │   ├── inventory/
│   │   ├── reservations/
│   │   ├── channels/
│   │   ├── notifications/
│   │   └── settings/
│   ├── router/
│   │   ├── index.tsx                 # Route config with lazy loading
│   │   ├── routes.ts                 # Path constants
│   │   ├── ProtectedRoute.tsx        # Auth guard
│   │   └── RoleGuard.tsx             # Role-based route guard
│   └── styles/
│       └── globals.css               # Tailwind base + CSS variables
├── Dockerfile
│   # Multi-stage: build React → serve via nginx
│   # FROM node:20-slim AS build
│   # RUN npm ci && npm run build
│   # FROM nginx:alpine
│   # COPY --from=build /app/dist /usr/share/nginx/html
│   # COPY nginx.conf /etc/nginx/conf.d/default.conf
├── nginx.conf
│   # SPA routing: try_files $uri /index.html
│   # Proxy /api to Kong gateway in K8s
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts
```

## API Client (with JWT refresh)

```typescript
// src/lib/api-client.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth-store';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const refresh = useAuthStore.getState().refreshToken;
        const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refresh });
        useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;
        return apiClient(original);
      } catch {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

## Service Layer Pattern
Each feature module has `services/<name>-service.ts` with API call functions, consumed by TanStack Query hooks:

```typescript
// features/rooms/services/rooms-service.ts
export const roomsService = {
  list: (params) => apiClient.get('/rooms/types', { params }),
  getById: (id) => apiClient.get(`/rooms/types/${id}`),
  create: (data) => apiClient.post('/rooms/types', data),
  update: (id, data) => apiClient.patch(`/rooms/types/${id}`, data),
  delete: (id) => apiClient.delete(`/rooms/types/${id}`),
};

// Used in components:
export function useRoomTypes() {
  return useQuery({ queryKey: ['room-types'], queryFn: () => roomsService.list().then(r => r.data) });
}
```
