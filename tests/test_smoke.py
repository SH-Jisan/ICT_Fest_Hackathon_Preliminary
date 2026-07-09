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

    # 1b. Test Back-to-Back booking: OK (starts exactly at end_1)
    start_b2b = end_1
    end_b2b = start_b2b + timedelta(hours=1)
    res_b2b = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_b2b.isoformat(), "end_time": end_b2b.isoformat()},
        headers=headers,
    )
    assert res_b2b.status_code == 201
    assert res_b2b.json()["price_cents"] == 1000

    # 1c. Test Overlapping booking: Fail (409 ROOM_CONFLICT)
    start_overlap = start_1 + timedelta(minutes=30)
    end_overlap = start_overlap + timedelta(hours=1)
    res_overlap = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_overlap.isoformat(), "end_time": end_overlap.isoformat()},
        headers=headers,
    )
    assert res_overlap.status_code == 409
    assert res_overlap.json()["code"] == "ROOM_CONFLICT"

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


def test_booking_quota_limits():
    org = f"quota-acme-{datetime.now().timestamp()}"
    reg = client.post(
        "/auth/register",
        json={"org_name": org, "username": "quota_alice", "password": "pw12345"},
    )
    assert reg.status_code == 201
    token = client.post(
        "/auth/login",
        json={"org_name": org, "username": "quota_alice", "password": "pw12345"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    room_id = client.post(
        "/rooms",
        json={"name": "Quota Room", "capacity": 4, "hourly_rate_cents": 1000},
        headers=headers,
    ).json()["id"]

    now = datetime.now(timezone.utc)
    # Create 3 bookings within the next 24 hours:
    # Booking 1: now + 2h -> now + 3h
    start_1 = (now + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)
    end_1 = start_1 + timedelta(hours=1)
    res_1 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_1.isoformat(), "end_time": end_1.isoformat()},
        headers=headers,
    )
    assert res_1.status_code == 201

    # Booking 2: now + 5h -> now + 6h
    start_2 = (now + timedelta(hours=5)).replace(minute=0, second=0, microsecond=0)
    end_2 = start_2 + timedelta(hours=1)
    res_2 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_2.isoformat(), "end_time": end_2.isoformat()},
        headers=headers,
    )
    assert res_2.status_code == 201

    # Booking 3: now + 8h -> now + 9h
    start_3 = (now + timedelta(hours=8)).replace(minute=0, second=0, microsecond=0)
    end_3 = start_3 + timedelta(hours=1)
    res_3 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_3.isoformat(), "end_time": end_3.isoformat()},
        headers=headers,
    )
    assert res_3.status_code == 201

    # Booking 4 (in the 24h window): should FAIL
    start_4 = (now + timedelta(hours=11)).replace(minute=0, second=0, microsecond=0)
    end_4 = start_4 + timedelta(hours=1)
    res_4 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_4.isoformat(), "end_time": end_4.isoformat()},
        headers=headers,
    )
    assert res_4.status_code == 409
    assert res_4.json()["code"] == "QUOTA_EXCEEDED"

    # Booking 5 (outside the 24h window): should SUCCEED
    start_5 = (now + timedelta(hours=30)).replace(minute=0, second=0, microsecond=0)
    end_5 = start_5 + timedelta(hours=1)
    res_5 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_5.isoformat(), "end_time": end_5.isoformat()},
        headers=headers,
    )
    assert res_5.status_code == 201


def test_rate_limiting():
    org = f"rate-acme-{datetime.now().timestamp()}"
    reg = client.post(
        "/auth/register",
        json={"org_name": org, "username": "rate_alice", "password": "pw12345"},
    )
    assert reg.status_code == 201
    token = client.post(
        "/auth/login",
        json={"org_name": org, "username": "rate_alice", "password": "pw12345"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Hit the bookings endpoint 20 times with invalid data (will fail with 400, but counts)
    for _ in range(20):
        res = client.post(
            "/bookings",
            json={"room_id": 99999, "start_time": "invalid-time", "end_time": "invalid-time"},
            headers=headers,
        )
        assert res.status_code == 400
        assert res.json()["code"] == "INVALID_BOOKING_WINDOW"

    # The 21st request should be blocked by the rate limiter (returns 429 RATE_LIMITED)
    res_21 = client.post(
        "/bookings",
        json={"room_id": 99999, "start_time": "invalid-time", "end_time": "invalid-time"},
        headers=headers,
    )
    assert res_21.status_code == 429
    assert res_21.json()["code"] == "RATE_LIMITED"


def test_cancellation_and_refund_policy():
    org = f"refund-acme-{datetime.now().timestamp()}"
    # Register admin (first user)
    reg_admin = client.post(
        "/auth/register",
        json={"org_name": org, "username": "ref_admin", "password": "pw12345"},
    )
    assert reg_admin.status_code == 201
    token_admin = client.post(
        "/auth/login",
        json={"org_name": org, "username": "ref_admin", "password": "pw12345"},
    ).json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # Register member (second user)
    reg_member = client.post(
        "/auth/register",
        json={"org_name": org, "username": "ref_member", "password": "pw12345"},
    )
    assert reg_member.status_code == 201
    token_member = client.post(
        "/auth/login",
        json={"org_name": org, "username": "ref_member", "password": "pw12345"},
    ).json()["access_token"]
    headers_member = {"Authorization": f"Bearer {token_member}"}

    # Create room with hourly rate 1001 cents (to test half-cent rounding up: 50% of 1001 is 500.5 -> 501)
    room = client.post(
        "/rooms",
        json={"name": "Refund Room", "capacity": 4, "hourly_rate_cents": 1001},
        headers=headers_admin,
    )
    assert room.status_code == 201
    room_id = room.json()["id"]

    now = datetime.now(timezone.utc)

    # 1. 100% Refund (notice >= 48 hours)
    start_48 = (now + timedelta(hours=50)).replace(minute=0, second=0, microsecond=0)
    end_48 = start_48 + timedelta(hours=1)
    b_48_id = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_48.isoformat(), "end_time": end_48.isoformat()},
        headers=headers_member,
    ).json()["id"]

    # Cancel 48h booking: should get 100% refund (1001 cents)
    res_cancel_48 = client.post(f"/bookings/{b_48_id}/cancel", headers=headers_member)
    assert res_cancel_48.status_code == 200
    assert res_cancel_48.json()["refund_percent"] == 100
    assert res_cancel_48.json()["refund_amount_cents"] == 1001

    # Check database RefundLog equals response via GET /bookings/{id}
    b_48_detail = client.get(f"/bookings/{b_48_id}", headers=headers_member).json()
    assert len(b_48_detail["refunds"]) == 1
    assert b_48_detail["refunds"][0]["amount_cents"] == 1001

    # 2. 50% Refund (24 <= notice < 48 hours) & Half-cent rounding up (1001 * 50% = 500.5 -> 501)
    start_24 = (now + timedelta(hours=30)).replace(minute=0, second=0, microsecond=0)
    end_24 = start_24 + timedelta(hours=1)
    b_24_id = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_24.isoformat(), "end_time": end_24.isoformat()},
        headers=headers_member,
    ).json()["id"]

    # Cancel 24h booking: should get 50% refund rounded up (501 cents)
    res_cancel_24 = client.post(f"/bookings/{b_24_id}/cancel", headers=headers_member)
    assert res_cancel_24.status_code == 200
    assert res_cancel_24.json()["refund_percent"] == 50
    assert res_cancel_24.json()["refund_amount_cents"] == 501

    # Check database RefundLog equals 501
    b_24_detail = client.get(f"/bookings/{b_24_id}", headers=headers_member).json()
    assert b_24_detail["refunds"][0]["amount_cents"] == 501

    # 3. 0% Refund (notice < 24 hours)
    start_12 = (now + timedelta(hours=12)).replace(minute=0, second=0, microsecond=0)
    end_12 = start_12 + timedelta(hours=1)
    b_12_id = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_12.isoformat(), "end_time": end_12.isoformat()},
        headers=headers_member,
    ).json()["id"]

    # Cancel 12h booking: should get 0% refund (0 cents)
    res_cancel_12 = client.post(f"/bookings/{b_12_id}/cancel", headers=headers_member)
    assert res_cancel_12.status_code == 200
    assert res_cancel_12.json()["refund_percent"] == 0
    assert res_cancel_12.json()["refund_amount_cents"] == 0

    # 4. Already Cancelled (returns 409)
    res_cancel_dup = client.post(f"/bookings/{b_12_id}/cancel", headers=headers_member)
    assert res_cancel_dup.status_code == 409
    assert res_cancel_dup.json()["code"] == "ALREADY_CANCELLED"

    # 5. Admin of the same organization can cancel member's booking
    start_adm = (now + timedelta(hours=40)).replace(minute=0, second=0, microsecond=0)
    end_adm = start_adm + timedelta(hours=1)
    b_adm_id = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_adm.isoformat(), "end_time": end_adm.isoformat()},
        headers=headers_member,
    ).json()["id"]

    res_cancel_adm = client.post(f"/bookings/{b_adm_id}/cancel", headers=headers_admin)
    assert res_cancel_adm.status_code == 200
    assert res_cancel_adm.json()["status"] == "cancelled"


def test_reference_code_seeding_and_collision():
    from app.services import reference
    org = f"refcode-acme-{datetime.now().timestamp()}"
    reg = client.post(
        "/auth/register",
        json={"org_name": org, "username": "refcode_alice", "password": "pw12345"},
    )
    assert reg.status_code == 201
    token = client.post(
        "/auth/login",
        json={"org_name": org, "username": "refcode_alice", "password": "pw12345"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    room_id = client.post(
        "/rooms",
        json={"name": "Refcode Room", "capacity": 4, "hourly_rate_cents": 1000},
        headers=headers,
    ).json()["id"]

    now = datetime.now(timezone.utc)
    
    # 1. Create first booking
    start_1 = (now + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)
    end_1 = start_1 + timedelta(hours=1)
    res_1 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_1.isoformat(), "end_time": end_1.isoformat()},
        headers=headers,
    )
    assert res_1.status_code == 201
    code_1 = res_1.json()["reference_code"]
    
    # 2. Simulate server restart by resetting in-memory counter back to 1000
    reference._counter["value"] = 1000
    
    # 3. Create second booking (should query DB for max existing code, seed, and succeed!)
    start_2 = (now + timedelta(hours=5)).replace(minute=0, second=0, microsecond=0)
    end_2 = start_2 + timedelta(hours=1)
    res_2 = client.post(
        "/bookings",
        json={"room_id": room_id, "start_time": start_2.isoformat(), "end_time": end_2.isoformat()},
        headers=headers,
    )
    assert res_2.status_code == 201
    code_2 = res_2.json()["reference_code"]
    
    # Verify codes are distinct and incremented
    assert code_1 != code_2
    num_1 = int(code_1.split("-")[1])
    num_2 = int(code_2.split("-")[1])
    assert num_2 > num_1


def test_auth_logout_and_refresh_rotation():
    org = f"jwt-acme-{datetime.now().timestamp()}"
    # 1. Register and login
    reg = client.post(
        "/auth/register",
        json={"org_name": org, "username": "jwt_alice", "password": "pw12345"},
    )
    assert reg.status_code == 201
    
    tokens = client.post(
        "/auth/login",
        json={"org_name": org, "username": "jwt_alice", "password": "pw12345"},
    ).json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 2. Test access token works on protected endpoint
    res_rooms = client.get("/rooms", headers=headers)
    assert res_rooms.status_code == 200
    
    # 3. Perform logout
    res_logout = client.post("/auth/logout", headers=headers)
    assert res_logout.status_code == 200
    
    # 4. Access token must be rejected after logout
    res_rooms_after = client.get("/rooms", headers=headers)
    assert res_rooms_after.status_code == 401
    assert res_rooms_after.json()["code"] == "UNAUTHORIZED"
    
    # Logout again with same token: must fail
    res_logout_after = client.post("/auth/logout", headers=headers)
    assert res_logout_after.status_code == 401
    assert res_logout_after.json()["code"] == "UNAUTHORIZED"

    # 5. Test refresh token rotation
    res_refresh = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res_refresh.status_code == 200
    new_tokens = res_refresh.json()
    assert new_tokens["access_token"] != access_token
    assert new_tokens["refresh_token"] != refresh_token
    
    # 6. Reusing old refresh token must be rejected
    res_refresh_dup = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res_refresh_dup.status_code == 401
    assert res_refresh_dup.json()["code"] == "UNAUTHORIZED"







