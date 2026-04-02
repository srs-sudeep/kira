---
sidebar_position: 3
---

# State Management

KIRA uses two complementary state systems with clear separation of concerns.

## TanStack Query — Server State

All data fetched from the API lives in TanStack Query. **Never** put API data in Zustand.

### Query Keys

All query keys are defined in `src/config/constants.ts`:

```typescript
export const QUERY_KEYS = {
  AUTH: {
    ME: ['auth', 'me'],
  },
  RATES: {
    ROOM_TYPES: ['rates', 'room-types'],
    RATE_PLANS: (roomTypeId?: string) => ['rates', 'rate-plans', roomTypeId],
    ARI: (params?: ARIParams) => ['rates', 'ari', params],
  },
  RESERVATIONS: {
    LIST: (filters?: ReservationFilters) => ['reservations', 'list', filters],
    DETAIL: (id: string) => ['reservations', 'detail', id],
  },
  CHANNELS: {
    LIST: ['channels', 'list'],
    DETAIL: (id: string) => ['channels', 'detail', id],
    SYNC_LOG: (id: string) => ['channels', 'sync-log', id],
  },
  NOTIFICATIONS: {
    LIST: (filters?: NotificationFilters) => ['notifications', 'list', filters],
    UNREAD_COUNT: ['notifications', 'unread-count'],
    PREFERENCES: ['notifications', 'preferences'],
  },
  SETTINGS: {
    PROPERTY: ['settings', 'property'],
    AUDIT_LOG: (filters?: AuditLogFilters) => ['settings', 'audit-log', filters],
  },
  USERS: {
    LIST: ['users', 'list'],
    DETAIL: (id: string) => ['users', 'detail', id],
  },
} as const;
```

### Invalidation Strategy

After mutations, invalidate the relevant query keys:

```typescript
const updateRateMutation = useMutation({
  mutationFn: ratesService.updateRatePlan,
  onSuccess: (_, variables) => {
    // Invalidate the specific detail
    queryClient.invalidateQueries({
      queryKey: QUERY_KEYS.RATES.RATE_PLANS(variables.roomTypeId),
    });
    // Also invalidate ARI since rates may affect displayed data
    queryClient.invalidateQueries({
      queryKey: ['rates', 'ari'],
    });
  },
});
```

## Zustand — Client State

Zustand stores only UI state and auth tokens — data that is **not** fetched from the API.

### Auth Store

```typescript
// src/stores/authStore.ts
interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  login: (user: User, accessToken: string) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  setAccessToken: (token: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      login: (user, accessToken) =>
        set({ user, accessToken, isAuthenticated: true }),
      logout: () =>
        set({ user: null, accessToken: null, isAuthenticated: false }),
      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
      setAccessToken: (token) => set({ accessToken: token }),
    }),
    { name: 'kira-auth' }
  )
);
```

### UI Store

```typescript
// src/stores/uiStore.ts
interface UIState {
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark' | 'system';
  toggleSidebar: () => void;
  setTheme: (theme: UIState['theme']) => void;
}
```

## What Goes Where

| Data | Storage | Why |
|---|---|---|
| Room types, rate plans | TanStack Query | Fetched from API, needs cache invalidation |
| Reservation list | TanStack Query | Server-paginated, filtered |
| Unread notification count | TanStack Query | Polled every 30s |
| Current user profile | TanStack Query (`QUERY_KEYS.AUTH.ME`) | Up-to-date from server |
| Access token | Zustand (persisted) | Needed for axios interceptor |
| User object (for header display) | Zustand | Avoids extra fetch on every page |
| Sidebar collapsed state | Zustand | Pure UI preference |
| Active filters (in-memory) | `useState` | Component-local, not shared |
| Form input state | React Hook Form | Component-local |
