"""Happy-path smoke test covering the core booking flow.

Run with ``pytest`` after installing requirements. It exercises a single,
sequential golden path and is not a substitute for full API testing.
"""
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _future(hours: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).replace(
        minute=0, second=0, microsecond=0
    ).isoformat()


def test_core_flow():
    assert client.get("/health").json() == {"status": "ok"}

    org = f"acme-{datetime.now().timestamp()}"
    reg = client.post(
        "/auth/register",
        json={"org_name": org, "username": "alice", "password": "pw12345"},
    )
    assert reg.status_code == 201
    assert reg.json()["role"] == "admin"

    login = client.post(
        "/auth/login",
        json={"org_name": org, "username": "alice", "password": "pw12345"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    room = client.post(
        "/rooms",
        json={"name": "Focus Room", "capacity": 4, "hourly_rate_cents": 1000},
        headers=headers,
    )
    assert room.status_code == 201
    room_id = room.json()["id"]

    booking = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": _future(50), "end_time": _future(52)},
        headers=headers,
    )
    assert booking.status_code == 201
    assert booking.json()["price_cents"] == 2000

    listing = client.get("/bookings", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1


def test_timezone_offset_handling():
    org = f"tz-acme-{datetime.now().timestamp()}"
    reg = client.post(
        "/auth/register",
        json={"org_name": org, "username": "tz_alice", "password": "pw12345"},
    )
    assert reg.status_code == 201
    token = client.post(
        "/auth/login",
        json={"org_name": org, "username": "tz_alice", "password": "pw12345"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    room_id = client.post(
        "/rooms",
        json={"name": "Tz Room", "capacity": 4, "hourly_rate_cents": 1000},
        headers=headers,
    ).json()["id"]

    # Use a future start time with +06:00 offset
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).date()
    start_str = f"{future_date}T18:00:00+06:00"
    end_str = f"{future_date}T20:00:00+06:00"

    # Expected UTC converted time: 18:00 - 6 hours = 12:00 UTC
    expected_start_utc = f"{future_date}T12:00:00+00:00"
    expected_end_utc = f"{future_date}T14:00:00+00:00"

    booking = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_str, "end_time": end_str},
        headers=headers,
    )
    assert booking.status_code == 201
    b_data = booking.json()
    assert b_data["start_time"] == expected_start_utc
    assert b_data["end_time"] == expected_end_utc

    # Test invalid validation format returns 400
    bad_booking = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": "invalid-datetime", "end_time": end_str},
        headers=headers,
    )
    assert bad_booking.status_code == 400
    assert bad_booking.json()["code"] == "INVALID_BOOKING_WINDOW"

