---
sidebar_position: 2
---

# Frontend Architecture

## Routing

React Router 7 with nested routes. The root layout wraps all authenticated pages.

```
/                     → AppShell layout
├── /                 → DashboardPage (index)
├── /rates            → RatesPage
├── /reservations     → ReservationsPage
├── /reservations/:id → ReservationDetailPage
├── /channels         → ChannelsPage
├── /channels/:id     → ChannelDetailPage
├── /notifications    → NotificationsPage
├── /profile          → ProfilePage
└── /settings         → SettingsPage (layout with outlet)
    ├── (index)       → PropertySettingsPage
    ├── /users        → UserManagementPage
    └── /audit-log    → AuditLogPage

/login                → LoginPage (no AppShell)
/register             → RegisterPage (no AppShell)
```

All authenticated routes use a `<ProtectedRoute>` wrapper that redirects to `/login` if no valid access token exists in Zustand.

## API Layer

Each feature has a service file that wraps `apiClient` (an axios instance with auth interceptors):

```typescript
// src/features/rates/services/ratesService.ts
export const ratesService = {
  getRoomTypes: () =>
    apiClient.get<RoomType[]>('/rates/room-types/').then(r => r.data),

  createRoomType: (data: CreateRoomTypeRequest) =>
    apiClient.post<RoomType>('/rates/room-types/', data).then(r => r.data),
};
```

The axios instance automatically:
- Attaches `Authorization: Bearer <token>` from Zustand
- Refreshes the access token on 401 responses (silent refresh)
- Redirects to login if refresh also fails

## Data Fetching Pattern

```typescript
// Page component
const { data, isLoading, error } = useQuery({
  queryKey: QUERY_KEYS.RATES.ROOM_TYPES,
  queryFn: ratesService.getRoomTypes,
});

// Mutation
const createMutation = useMutation({
  mutationFn: ratesService.createRoomType,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: QUERY_KEYS.RATES.ROOM_TYPES });
    toast.success('Room type created');
  },
});
```

## Form Pattern

All forms use React Hook Form with Zod validation:

```typescript
const schema = z.object({
  name: z.string().min(1, 'Required'),
  max_occupancy: z.number().min(1).max(20),
});

type FormData = z.infer<typeof schema>;

const form = useForm<FormData>({
  resolver: zodResolver(schema),
  defaultValues: { name: '', max_occupancy: 2 },
});
```

For edit forms that populate from an API query, use `values:` (not `defaultValues:`) so the form re-initializes when data loads:

```typescript
const form = useForm<FormData>({
  resolver: zodResolver(schema),
  values: data ? { name: data.name, max_occupancy: data.max_occupancy } : undefined,
});
```

## Component Conventions

- `PascalCase` for component files and functions
- `kebab-case` for file names
- `camelCase` for functions, variables, and hooks
- All base UI elements from shadcn/ui — never write raw `<input>` or `<button>` tags
- `cn()` from `lib/utils` for conditional class merging

```tsx
// Good
<Button variant="destructive" onClick={handleDelete}>Delete</Button>

// Bad — don't use raw HTML
<button className="btn-danger" onClick={handleDelete}>Delete</button>
```

## TypeScript Rules

- `strict: true` in tsconfig — no escape hatches
- No `any` — use `unknown` and narrow with type guards
- All API responses typed against generated/manual types in `src/types/`
- All query key factories typed with `as const` or return type annotation
