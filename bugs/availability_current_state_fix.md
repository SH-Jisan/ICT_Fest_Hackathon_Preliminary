# Bug: Stale Room Availability Cache on Cancellation

## Summary
The room availability endpoint `GET /rooms/{id}/availability` returned stale cached busy schedules because the booking cancellation endpoint did not invalidate the availability cache for the booking's room and date.

## Rule Violated
> **The endpoint must always reflect the latest committed database state immediately. Recently cancelled bookings must immediately disappear in the availability response. No stale cache may be returned.**

## Severity
High

## Affected Files
* [app/routers/bookings.py](file:///d:/ICT_Fest_Hackathon_Preliminary/app/routers/bookings.py)

## Modified Line Numbers
* `bookings.py` : Line 230

## Original Code
```python
    stats.record_cancel(booking.room_id, booking.price_cents)
    cache.invalidate_report(user.org_id)
    notifications.notify_cancelled(booking)
```

## Fixed Code
```python
    stats.record_cancel(booking.room_id, booking.price_cents)
    cache.invalidate_availability(booking.room_id, booking.start_time.date().isoformat())
    cache.invalidate_report(user.org_id)
    notifications.notify_cancelled(booking)
```

## Root Cause
Missed availability cache invalidation logic on cancellation.

## Fix Applied
Added `cache.invalidate_availability(booking.room_id, booking.start_time.date().isoformat())` inside `cancel_booking`.

## Why the Fix Works
Guarantees that cancelling any booking immediately clears the room's availability cache for that specific date, forcing the next availability request to load fresh, up-to-date data from the database.

## Performance & Concurrency Notes
Ensures real-time caching consistency without database query degradation or race condition risks.

## Tests Updated
Added `test_room_availability_current_state` integration test in [test_smoke.py](file:///d:/ICT_Fest_Hackathon_Preliminary/tests/test_smoke.py#L790-L839).
