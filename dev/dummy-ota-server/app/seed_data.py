"""Static dummy hotels, room types, rate plans, and reservations for local dev."""

from __future__ import annotations

from datetime import date, timedelta

TODAY = date.today()

HOTELS = [
    {
        "hotel_id": "DUMMY-BDC-001",
        "ota": "booking_com",
        "name": "Grand Plaza (Dummy Booking.com)",
        "currency": "USD",
        "timezone": "America/New_York",
        "address": {"line1": "100 Mock St", "city": "New York", "country": "US"},
    },
    {
        "hotel_id": "DUMMY-EXP-001",
        "ota": "expedia",
        "name": "Seaside Inn (Dummy Expedia)",
        "currency": "EUR",
        "timezone": "Europe/Paris",
        "address": {"line1": "2 Rue Factice", "city": "Nice", "country": "FR"},
    },
    {
        "hotel_id": "DUMMY-MMT-001",
        "ota": "makemytrip",
        "name": "Lakeview Resort (Dummy MMT)",
        "currency": "INR",
        "timezone": "Asia/Kolkata",
        "address": {"line1": "7 MG Road", "city": "Goa", "country": "IN"},
    },
]

ROOM_TYPES = {
    "DUMMY-BDC-001": [
        {"ota_room_type_id": "BDC-RT-DLX", "name": "Deluxe King", "max_occupancy": 3},
        {"ota_room_type_id": "BDC-RT-STD", "name": "Standard Twin", "max_occupancy": 2},
    ],
    "DUMMY-EXP-001": [
        {"ota_room_type_id": "EXP-RT-OCEAN", "name": "Ocean View Suite", "max_occupancy": 4},
    ],
    "DUMMY-MMT-001": [
        {"ota_room_type_id": "MMT-RT-VILLA", "name": "Garden Villa", "max_occupancy": 6},
        {"ota_room_type_id": "MMT-RT-DLX", "name": "Deluxe Room", "max_occupancy": 3},
    ],
}

RATE_PLANS = {
    "DUMMY-BDC-001": [
        {"ota_rate_plan_id": "BDC-RP-BAR", "name": "Best Available"},
        {"ota_rate_plan_id": "BDC-RP-NRF", "name": "Non-refundable"},
    ],
    "DUMMY-EXP-001": [
        {"ota_rate_plan_id": "EXP-RP-PACK", "name": "Package Rate"},
    ],
    "DUMMY-MMT-001": [
        {"ota_rate_plan_id": "MMT-RP-AP", "name": "Advance Purchase"},
    ],
}


def _reservations() -> list[dict]:
    """Several reservations across hotels with stable IDs for demos."""
    ci = TODAY + timedelta(days=2)
    co = ci + timedelta(days=3)
    return [
        {
            "reservation_id": "DUMMY-RES-BDC-1001",
            "hotel_id": "DUMMY-BDC-001",
            "ota": "booking_com",
            "status": "confirmed",
            "channel_confirmation_id": "BDC-778899001",
            "ota_room_type_id": "BDC-RT-DLX",
            "ota_rate_plan_id": "BDC-RP-BAR",
            "check_in": ci.isoformat(),
            "check_out": co.isoformat(),
            "nights": (co - ci).days,
            "adults": 2,
            "children": 1,
            "total_amount": "1249.00",
            "currency": "USD",
            "guest": {
                "first_name": "Alex",
                "last_name": "Rivera",
                "email": "alex.rivera@example.com",
                "phone": "+1-555-0100",
            },
            "special_requests": "High floor, away from elevator",
            "created_at": (TODAY - timedelta(days=5)).isoformat() + "T14:22:00Z",
        },
        {
            "reservation_id": "DUMMY-RES-BDC-1002",
            "hotel_id": "DUMMY-BDC-001",
            "ota": "booking_com",
            "status": "confirmed",
            "channel_confirmation_id": "BDC-778899002",
            "ota_room_type_id": "BDC-RT-STD",
            "ota_rate_plan_id": "BDC-RP-NRF",
            "check_in": (TODAY + timedelta(days=10)).isoformat(),
            "check_out": (TODAY + timedelta(days=12)).isoformat(),
            "nights": 2,
            "adults": 1,
            "children": 0,
            "total_amount": "289.50",
            "currency": "USD",
            "guest": {
                "first_name": "Sam",
                "last_name": "Okonkwo",
                "email": "sam.ok@example.com",
            },
            "created_at": (TODAY - timedelta(days=1)).isoformat() + "T09:05:00Z",
        },
        {
            "reservation_id": "DUMMY-RES-EXP-2001",
            "hotel_id": "DUMMY-EXP-001",
            "ota": "expedia",
            "status": "confirmed",
            "channel_confirmation_id": "EXP-EQC-44102",
            "ota_room_type_id": "EXP-RT-OCEAN",
            "ota_rate_plan_id": "EXP-RP-PACK",
            "check_in": (TODAY + timedelta(days=1)).isoformat(),
            "check_out": (TODAY + timedelta(days=5)).isoformat(),
            "nights": 4,
            "adults": 2,
            "children": 0,
            "total_amount": "1820.00",
            "currency": "EUR",
            "guest": {
                "first_name": "Marie",
                "last_name": "Dubois",
                "email": "marie.dubois@example.fr",
                "phone": "+33-6-12-34-56-78",
            },
            "created_at": TODAY.isoformat() + "T11:30:00Z",
        },
        {
            "reservation_id": "DUMMY-RES-MMT-3001",
            "hotel_id": "DUMMY-MMT-001",
            "ota": "makemytrip",
            "status": "confirmed",
            "channel_confirmation_id": "MMT-9988776655",
            "ota_room_type_id": "MMT-RT-VILLA",
            "ota_rate_plan_id": "MMT-RP-AP",
            "check_in": (TODAY + timedelta(days=7)).isoformat(),
            "check_out": (TODAY + timedelta(days=10)).isoformat(),
            "nights": 3,
            "adults": 4,
            "children": 2,
            "total_amount": "94500.00",
            "currency": "INR",
            "guest": {
                "first_name": "Priya",
                "last_name": "Sharma",
                "email": "priya.s@example.in",
            },
            "special_requests": "Late check-in after 11pm",
            "created_at": (TODAY - timedelta(days=2)).isoformat() + "T16:00:00Z",
        },
        {
            "reservation_id": "DUMMY-RES-MMT-3002",
            "hotel_id": "DUMMY-MMT-001",
            "ota": "makemytrip",
            "status": "cancelled",
            "channel_confirmation_id": "MMT-1122334400",
            "ota_room_type_id": "MMT-RT-DLX",
            "ota_rate_plan_id": "MMT-RP-AP",
            "check_in": (TODAY + timedelta(days=20)).isoformat(),
            "check_out": (TODAY + timedelta(days=22)).isoformat(),
            "nights": 2,
            "adults": 2,
            "children": 0,
            "total_amount": "0.00",
            "currency": "INR",
            "guest": {
                "first_name": "Rahul",
                "last_name": "Verma",
                "email": "rahul.v@example.in",
            },
            "created_at": (TODAY - timedelta(days=10)).isoformat() + "T08:00:00Z",
        },
    ]


RESERVATIONS: list[dict] = _reservations()


def inventory_snapshot(hotel_id: str) -> list[dict]:
    """14 days of dummy availability/rates per room+rate combo for one hotel."""
    rts = ROOM_TYPES.get(hotel_id, [])
    rps = RATE_PLANS.get(hotel_id, [])
    rows: list[dict] = []
    for d in range(14):
        day = TODAY + timedelta(days=d)
        for rt in rts:
            for rp in rps:
                base = 120 + d * 3 + hash(rt["ota_room_type_id"]) % 40
                rows.append(
                    {
                        "date": day.isoformat(),
                        "ota_room_type_id": rt["ota_room_type_id"],
                        "ota_rate_plan_id": rp["ota_rate_plan_id"],
                        "available_rooms": 5 if d % 7 != 6 else 0,
                        "rate": str(base + 0.99),
                        "closed": d % 7 == 6,
                        "min_los": 1,
                        "max_los": 14,
                    }
                )
    return rows
