---
title: First Run
description: Walkthrough of creating a hotel tenant, adding room types, making a reservation, and exploring the KIRA dashboard.
sidebar_position: 3
---

# First Run Walkthrough

**What you'll learn:**
- How to log in as super-admin and create a new hotel tenant
- How to create room types and rate plans
- How to make a manual reservation and view it in the dashboard
- Where notifications appear and how to configure preferences
- What each dashboard KPI card tracks

:::info Prerequisite
Complete [Local Setup](./local-setup.md) first. The stack must be running (`docker compose ps` shows all services healthy) and you should have the seeded credentials available.
:::

<!-- TODO: add screenshots -->

---

## 1. Log In as Super-Admin

Open [http://localhost:3000/login](http://localhost:3000/login).

Use the super-admin credentials created during seeding:

| Field | Value |
|---|---|
| Email | `admin@kira.local` |
| Password | `Admin1234!` |

After login you land on the **Dashboard** page. As super-admin, the sidebar shows an extra **Admin** section that hotel-role users cannot see.

<!-- TODO: add screenshot of dashboard -->

---

## 2. Create a New Tenant (Hotel Property)

:::note
This step is only possible as `super_admin`. If you're building a feature for a specific hotel, skip to [Step 3](#3-switch-to-the-hotel-admin-account) and use the seeded hotel.
:::

1. In the sidebar, click **Admin** → **Tenants**
2. Click **New Tenant**
3. Fill in the form:

```
Hotel Name:     The Grand Example Hotel
City:           Mumbai
Country:        India
Currency:       INR
Timezone:       Asia/Kolkata
Star Rating:    4
Admin Email:    manager@example-hotel.local
```

4. Click **Create Tenant**

KIRA provisions a new PostgreSQL schema (`tenant_{uuid}`) and seeds it with default data. The admin email receives an invitation (visible in Mailhog at [localhost:8025](http://localhost:8025)).

You'll see the new tenant appear in the tenants list with status **Active**.

<!-- TODO: add screenshot of tenant creation form -->

---

## 3. Switch to the Hotel Admin Account

Log out of the super-admin account and log in as the hotel manager created during seeding:

| Field | Value |
|---|---|
| Email | `manager@grandhotel.local` |
| Password | `Manager1234!` |

The dashboard now shows data scoped to **Grand Hotel Demo** only — the per-tenant schema isolation is working.

---

## 4. Explore the Dashboard

The **Dashboard** (home page) shows live KPI cards:

| Card | What it shows |
|---|---|
| **Occupancy Today** | Percentage of rooms occupied tonight |
| **Revenue MTD** | Month-to-date room revenue |
| **Reservations Today** | Check-ins + check-outs happening today |
| **Channel Sync Status** | Number of active channels and last sync time |

Below the KPI cards: a 30-day occupancy chart and a table of the 10 most recent reservations.

<!-- TODO: add screenshot of dashboard KPIs -->

---

## 5. Add a Room Type

The seeded data already includes room types, but here's how to add a new one:

1. In the sidebar, click **Rates & Inventory**
2. Click the **Room Types** tab
3. Click **New Room Type**
4. Fill in:

```
Name:             Executive Suite
Code:             EXEC-STE
Description:      Top-floor suite with panoramic city view
Max Occupancy:    3
Base Occupancy:   2
Amenities:        wifi, air_conditioning, minibar, safe, bathtub, city_view
```

5. Click **Create**

The new room type appears in the grid.

<!-- TODO: add screenshot of room type form -->

---

## 6. Add a Rate Plan

Rate plans live under a room type:

1. Click the **Executive Suite** card to open its detail page
2. Click **Rate Plans** tab → **New Rate Plan**
3. Fill in:

```
Name:                Best Available Rate
Code:                BAR
Meal Plan:           Room Only
Cancellation Policy: Free cancellation (cancel up to 24h before)
```

4. Click **Create**

Now add ARI (Availability, Rates, Inventory) data so the room has a rate for the next 30 days:

1. On the room type detail page, click **ARI Calendar**
2. Click **Bulk Update**
3. Set:

```
From Date:        today
To Date:          30 days from today
Rate per night:   ₹8,500
Available Rooms:  2
Min Stay:         1 night
```

4. Click **Apply**

The calendar fills in with the rate data. If the channel engine is connected to an OTA, it would now push this ARI automatically.

<!-- TODO: add screenshot of ARI calendar filled -->

---

## 7. Create a Manual Reservation

1. In the sidebar, click **Reservations**
2. Click **New Reservation**
3. Fill in the form:

```
Channel:          Direct
Room Type:        Executive Suite
Rate Plan:        Best Available Rate
Check-in:         tomorrow
Check-out:        3 nights later
Adults:           2
Children:         0
Guest name:       Priya Sharma
Guest email:      priya.sharma@example.com
Guest phone:      +91-98765-43210
Special Requests: Late check-in after 10pm
```

4. Click **Confirm Reservation**

KIRA creates the reservation and:
- Decrements available rooms in the ARI calendar for those dates
- Publishes a `reservation.created` Kafka event
- Creates an in-app notification
- Sends a booking confirmation email (visible in Mailhog at [localhost:8025](http://localhost:8025))

<!-- TODO: add screenshot of new reservation form -->

---

## 8. Check the Notification Centre

After creating the reservation, click the **bell icon** in the top navigation bar.

A dropdown shows the most recent notification:
```
✅ New booking confirmed
   Booking #KIRA-2025-00001 for [check-in date]
```

Click **View All Notifications** to see the full archive. You can:
- Filter by type (reservation / channel / system)
- Mark individual notifications as read
- Bulk-mark all as read
- Configure email vs. in-app preferences per notification type

<!-- TODO: add screenshot of notification dropdown -->

---

## 9. View the Reservation Detail

Go back to **Reservations** and click the reservation you just created.

The detail page shows:
- Reservation status badge (`Confirmed`)
- Guest profile with contact info
- Stay details (room, dates, rate, total)
- Actions: **Modify**, **Check In**, **Cancel**
- Reservation notes (internal-only)

Try clicking **Modify** and changing the check-out date by one day. KIRA recalculates the total and updates ARI automatically.

<!-- TODO: add screenshot of reservation detail -->

---

## 10. Connect an OTA Channel (Optional)

To connect a real OTA channel, you need API credentials from the OTA's extranet:

1. In the sidebar, click **Channels**
2. Click **Connect Channel**
3. Select the OTA (Booking.com, Expedia, or MakeMyTrip)
4. Enter your API credentials
5. Click **Test Connection** — KIRA pings the OTA's API to validate
6. Click **Connect**
7. Map your room types and rate plans to the OTA's identifiers in the **Mappings** tab
8. Click **Sync Now** to push your ARI to the OTA immediately

If you don't have OTA credentials, you can use the **test mode** (mock adapter) in the `.env.local` for the channel engine.

<!-- TODO: add screenshot of channel connection wizard -->

---

## What's Next?

You've completed the first-run walkthrough. Here are natural next steps:

- **Understand the codebase** → [Project Structure](./project-structure.md)
- **Read the architecture** → [Architecture Overview](../architecture/overview.md)
- **Write your first feature** → [Contributing Guide](../contributing/development-setup.md)
- **Deploy to staging** → [Deployment Overview](../deployment/overview.md)
