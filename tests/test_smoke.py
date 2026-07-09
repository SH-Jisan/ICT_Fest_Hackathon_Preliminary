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


def test_booking_rules_compliance():
    org = f"rules-acme-{datetime.now().timestamp()}"
    reg = client.post(
        "/auth/register",
        json={"org_name": org, "username": "rules_alice", "password": "pw12345"},
    )
    token = client.post(
        "/auth/login",
        json={"org_name": org, "username": "rules_alice", "password": "pw12345"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    room_id = client.post(
        "/rooms",
        json={"name": "Rules Room", "capacity": 4, "hourly_rate_cents": 1000},
        headers=headers,
    ).json()["id"]

    # 1. Test 1-hour booking: OK
    now = datetime.now(timezone.utc)
    start_1 = (now + timedelta(days=1)).replace(minute=0, second=0, microsecond=0)
    end_1 = start_1 + timedelta(hours=1)
    res_1 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_1.isoformat(), "end_time": end_1.isoformat()},
        headers=headers,
    )
    assert res_1.status_code == 201
    assert res_1.json()["price_cents"] == 1000

    # 2. Test 8-hour booking: OK
    start_8 = (now + timedelta(days=2)).replace(minute=0, second=0, microsecond=0)
    end_8 = start_8 + timedelta(hours=8)
    res_8 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_8.isoformat(), "end_time": end_8.isoformat()},
        headers=headers,
    )
    assert res_8.status_code == 201
    assert res_8.json()["price_cents"] == 8000

    # 3. Test 9-hour booking: Fail (400)
    start_9 = (now + timedelta(days=3)).replace(minute=0, second=0, microsecond=0)
    end_9 = start_9 + timedelta(hours=9)
    res_9 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_9.isoformat(), "end_time": end_9.isoformat()},
        headers=headers,
    )
    assert res_9.status_code == 400
    assert res_9.json()["code"] == "INVALID_BOOKING_WINDOW"

    # 4. Test Fractional hours (e.g. 1.5 hours): Fail (400)
    end_frac = start_8 + timedelta(hours=1, minutes=30)
    res_frac = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_8.isoformat(), "end_time": end_frac.isoformat()},
        headers=headers,
    )
    assert res_frac.status_code == 400
    assert res_frac.json()["code"] == "INVALID_BOOKING_WINDOW"

    # 5. Test Past booking: Fail (400)
    start_past = now - timedelta(hours=2)
    end_past = now - timedelta(hours=1)
    res_past = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_past.isoformat(), "end_time": end_past.isoformat()},
        headers=headers,
    )
    assert res_past.status_code == 400
    assert res_past.json()["code"] == "INVALID_BOOKING_WINDOW"

    # 6. Test Equal start/request time: Fail (400)
    res_eq = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": now.isoformat(), "end_time": (now + timedelta(hours=1)).isoformat()},
        headers=headers,
    )
    assert res_eq.status_code == 400
    assert res_eq.json()["code"] == "INVALID_BOOKING_WINDOW"

    # 7. Test Invalid end time (end_time before start_time): Fail (400)
    res_inv_end = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_8.isoformat(), "end_time": (start_8 - timedelta(hours=2)).isoformat()},
        headers=headers,
    )
    assert res_inv_end.status_code == 400
    assert res_inv_end.json()["code"] == "INVALID_BOOKING_WINDOW"


