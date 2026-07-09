# Bug: Member Booking Detail Authorization Bypass

## Summary
The endpoint `GET /bookings/{booking_id}` loaded details for any booking in the organization without ensuring that members can only read their own bookings. Any member could query and read details of any other member's booking.

## Rule Violated
> **A member may read only their own bookings. If a member attempts to access another member's booking, the API must return HTTP 404 Not Found, BOOKING_NOT_FOUND.**

## Severity
Critical

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `bookings.py` : Lines 171–175

## Original Code
```python
    booking = (
        db.query(Booking)
        .join(Room, Booking.room_id == Room.id)
        .filter(Booking.id == booking_id, Room.org_id == user.org_id)
        .first()
    )
    if booking is None:
        raise AppError(404, "BOOKING_NOT_FOUND", "Booking not found")
```

## Fixed Code
```python
    booking = (
        db.query(Booking)
        .join(Room, Booking.room_id == Room.id)
        .filter(Booking.id == booking_id, Room.org_id == user.org_id)
        .first()
    )
    if booking is None:
        raise AppError(404, "BOOKING_NOT_FOUND", "Booking not found")

    if user.role != "admin" and booking.user_id != user.id:
        raise AppError(404, "BOOKING_NOT_FOUND", "Booking not found")
```

## Root Cause
Lacked user role and ownership verification.

## Fix Applied
Added validation to check if the caller is not an admin and is not the owner of the booking, raising a `404 BOOKING_NOT_FOUND` error if they are unauthorized.

## Why the Fix Works
Guarantees members can only read their own bookings. Returns `404 Not Found` with `BOOKING_NOT_FOUND` to prevent resource enumeration.

## Concurrency Notes
N/A

## Tests Updated
Added `test_member_booking_visibility_isolation` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L584-L654).
