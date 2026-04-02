---
title: Architecture Overview
description: High-level system topology, design principles, service ownership, and the communication matrix for the KIRA platform.
sidebar_position: 1
---

# Architecture Overview

**What you'll learn:**
- The full system topology from browser to database
- The four core design principles behind every architectural decision
- Which service owns which data (the golden rule)
- The communication matrix — who talks to whom and how

---

## System Topology

```mermaid
graph TD
    Browser["🌐 Browser / Mobile App"]
    Kong["Kong API Gateway :8000\n(routing · rate-limit · JWT verify · CORS)"]

    subgraph Services["Backend Services"]
        Identity["identity-service :8001\nauth · users · RBAC · MFA · audit"]
        RateInv["rate-inventory-service :8002\nroom types · rate plans · ARI calendar"]
        Res["reservation-service :8003\nbookings · guests · modifications"]
        Channel["channel-engine :8004\nOTA adapters · ARI push/pull · sync"]
        Notify["notification-service :8005\nemail · in-app · preferences"]
        Admin["admin-service :8006\ntenant onboarding · billing"]
    end

    subgraph Async["Async Event Bus"]
        Kafka["Apache Kafka\nari.updated · reservation.* · channel.sync.failed"]
    end

    subgraph OTAs["External OTA Channels"]
        BC["Booking.com\nConnectivity API"]
        EX["Expedia\nEQC API"]
        MMT["MakeMyTrip\nAPI"]
    end

    subgraph Data["Data Layer"]
        PG["PostgreSQL 16\npublic schema + tenant_{uuid} per hotel"]
        Redis["Redis 7\nsessions · rate-limit · circuit breaker state"]
    end

    Browser --> Kong
    Kong --> Identity
    Kong --> RateInv
    Kong --> Res
    Kong --> Channel
    Kong --> Notify
    Kong --> Admin

    RateInv -->|"ari.updated"| Kafka
    Res -->|"reservation.created\nreservation.cancelled"| Kafka
    Channel -->|"channel.sync.failed"| Kafka

    Kafka -->|"ari.updated"| Channel
    Kafka -->|"reservation.*\nchannel.sync.failed"| Notify

    Channel --> BC
    Channel --> EX
    Channel --> MMT

    Identity --> PG
    RateInv --> PG
    Res --> PG
    Channel --> PG
    Notify --> PG
    Admin --> PG

    Identity --> Redis
    Channel --> Redis
```

---

## Design Principles

### 1. Microservices — one domain per service

Each service does exactly one domain job. It has its own codebase, its own database tables, its own Docker image, and its own CI/CD pipeline. You can deploy the channel-engine without touching identity-service.

The boundary rule: **each service owns its data**. The channel-engine never writes directly to the `reservations` table. It publishes an event; reservation-service reacts and writes. This prevents tight coupling and keeps each service independently deployable.

### 2. Event-driven for ARI distribution

Rate and availability updates need to reach all connected OTAs after every change. Doing this synchronously in the request path (PUT /ari → call Booking.com API → call Expedia API → return to user) would make every ARI update take 5–30 seconds and fail if any OTA is temporarily down.

Instead: PUT /ari → save to DB → publish `ari.updated` to Kafka → return 200 immediately → channel-engine consumes the event and pushes to each OTA asynchronously. The UI shows "sync pending" and updates when complete.

### 3. Multi-tenant by schema isolation

All hotel properties share one PostgreSQL cluster. Each tenant gets its own schema (`tenant_{uuid_short}`). No `WHERE tenant_id = ?` clause required on every query — the database session has `search_path` set to the correct schema before the first query runs.

This approach provides hard data isolation (a bug cannot accidentally leak cross-tenant data), clean schema evolution (run migrations once per tenant schema), and good query performance (each tenant's indexes are their own).

### 4. Stateless pods, durable state in the data layer

Application pods hold no state in memory between requests. Sessions are in Redis. Business data is in PostgreSQL. This means any pod can handle any request, and adding replicas requires zero coordination.

---

## Service Ownership Table

The golden rule: if your service needs data it doesn't own, call the owning service's API or consume its events. Never write to another service's tables.

| Service | Port | Tables Owned | Kafka Topics Published |
|---|---|---|---|
| identity-service | 8001 | `public.users`, `public.refresh_tokens`, `public.audit_events` | — |
| admin-service | 8006 | `public.tenants` | `tenant.created` |
| rate-inventory-service | 8002 | `room_types`, `rate_plans`, `ari_snapshots`, `seasonal_rules`, `blackout_dates`, `inventory_history` | `ari.updated` |
| reservation-service | 8003 | `reservations`, `guest_profiles`, `reservation_notes` | `reservation.created`, `reservation.cancelled` |
| channel-engine | 8004 | `channels`, `channel_mappings`, `sync_logs` | `channel.sync.failed` |
| notification-service | 8005 | `notifications`, `notification_preferences` | — |

---

## Communication Matrix

| From → To | Transport | When | Example |
|---|---|---|---|
| Browser → any service | REST via Kong | All user-initiated actions | Login, create reservation |
| rate-inventory → channel-engine | Kafka `ari.updated` | After any ARI write | Rate changed, availability updated |
| reservation → channel-engine | Kafka `reservation.created` | Booking confirmed | Close availability on OTA |
| reservation → notification | Kafka `reservation.created` | Booking confirmed | Send confirmation email |
| reservation → notification | Kafka `reservation.cancelled` | Booking cancelled | Send cancellation email |
| channel-engine → notification | Kafka `channel.sync.failed` | OTA sync exhausted retries | Alert property manager |
| channel-engine → reservation | REST (internal) | OTA booking pulled | Create reservation record |
| any service → identity | REST (internal) | Token introspection | Validate JWT on protected routes |
| admin → identity | Kafka `tenant.created` | New hotel onboarded | Seed default roles |

For the full event catalog with schemas, see [Event-Driven Architecture](./event-driven.md).  
For REST API details, see [Communication Patterns](./communication.md).
